import uuid

from django.db import models
from django.core.cache import cache
from authentication.models import CustomUser, Student
from django.utils import timezone

from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes

from django.utils.translation import gettext as _
from django.db.models import Q

from dashboard.models import SiteSettings

from ..choices import *
from ..rules import *

from rules.contrib.models import RulesModel


# Create your models here.
class EventMainAttributes(RulesModel):
    active = models.BooleanField(default=True)

    lead_status = models.IntegerField(
        choices=LeadStatusChoices,
        default=1,
        help_text=_(
            "The lead status limits which parents are currently allowed to book this event. The lead status should be changed over time, otherwise not all parents will have the oportunity to book the event or an event which is part of this group."
        ),
    )

    lead_status_last_change = models.DateTimeField(default=timezone.now)

    lead_manual_override = models.BooleanField(default=False)

    disable_automatic_changes = models.BooleanField(
        default=False,
        help_text=_(
            "There are multiple functions in place which change the lead status according to the settings. If this box is checked, there will be no automatic updates to the lead status for this event or the events in this group."
        ),
    )

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        abstract = True


class EventGroupMainAttributes(EventMainAttributes):
    lead_start = models.DateField(
        default=timezone.now,
        help_text=_(
            "Set a date from which all parents can request appointments."
        ),  # Specify when all parents can book events
    )

    lead_inquiry_start = models.DateField(
        default=timezone.now,
        help_text=_(
            _(
                "Determine when teachers' enquiries can be answered."
            )  # Specify when parents with inquiries can start booking for corresponding events
        ),
    )

    force = models.BooleanField(default=False)

    manual_apply = models.BooleanField(default=False)

    class Meta:
        abstract = True


class BaseEventGroup(EventGroupMainAttributes):
    def get_default_valid_until():
        return timezone.now() + timezone.timedelta(days=7)

    valid_until = models.DateField(default=get_default_valid_until)

    def __str__(self):
        days = DayEventGroup.objects.filter(base_event=self).order_by("date")
        title_str = _(f"Parent-teacher conference on ")

        for index, day in enumerate(days):
            if index == 0:
                title_str += f"{day.date.strftime('%d.%m.%Y')}"
            elif index == days.count() - 1:
                title_str += _(" and ") + f"{day.date.strftime('%d.%m.%Y')}"
            else:
                title_str += f", {day.date.strftime('%d.%m.%Y')}"
        return title_str


class DayEventGroup(EventGroupMainAttributes):
    base_event = models.ForeignKey(BaseEventGroup, on_delete=models.CASCADE, null=True)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Event group - {str(self.date)}"


class TeacherEventGroup(EventGroupMainAttributes):
    day_group = models.ForeignKey(DayEventGroup, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, limit_choices_to={"role": 1}
    )

    lead_end_timedelta = models.DurationField(default=timezone.timedelta(hours=1))
    lead_allow_same_day = models.BooleanField(default=True)

    room = models.CharField(max_length=5, null=True, blank=True)

    def __str__(self):
        return f"{self.teacher} - {str(self.day_group.date)}"


class EventManager(models.Manager):
    def bulk_slots_create(
        self,
        teacher: CustomUser,
        start: timezone,
        end: timezone,
        duration: timezone.timedelta,
        bulk_mode=True,
        ignore_collisions=True,
    ):
        delta = end - start
        duration = SiteSettings.objects.all().first().event_duration
        total_count = int(delta / duration)

        bulk_time_slots_start = [
            start + duration * slot_num for slot_num in range(total_count)
        ]
        bulk_time_slots_end = bulk_time_slots_start.copy()
        bulk_time_slots_end.pop(0)
        bulk_time_slots_end.append(bulk_time_slots_end[-1] + duration)

        collision_events = Event.objects.filter(
            Q(teacher=teacher),
            Q(start__in=bulk_time_slots_start) | Q(end__in=bulk_time_slots_end),
            Q(active=True),
        )
        # print(collision_events)
        if collision_events.exists() and not ignore_collisions:
            raise ValueError(
                "There is a collision with an already existing, active event. Can´t proceed."
            )
        elif collision_events.exists():
            bulk_time_slots = [
                slot
                for slot in bulk_time_slots_start
                if not slot in list(collision_events.values_list("start", flat=True))
                or not slot + duration
                in list(collision_events.values_list("end", flat=True))
            ]
            # print([i for i in bulk_time_slots_start if not i in bulk_time_slots])
        else:
            bulk_time_slots = bulk_time_slots_start

        slot_objects = [
            Event(teacher=teacher, start=time_slot, end=time_slot + duration)
            for time_slot in bulk_time_slots
        ]
        if bulk_mode:
            events = Event.objects.bulk_create(slot_objects)
        else:  # needs much more time as pre_save and post_save signals are triggered.
            events = []
            for event_object in slot_objects:
                event = event_object
                event.save()
                events.append(event)
        return events


class Event(EventMainAttributes):
    base_event = models.ForeignKey(BaseEventGroup, on_delete=models.CASCADE)
    day_group = models.ForeignKey(DayEventGroup, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, limit_choices_to={"role": 1}
    )  # limit_choices_to={'role': 1} besagt, dass nur Nutzer, wo der Wert role glwich 1 ist eingesetzt werden können, also es wird verhindert, dass Eltern oder andere als Lehrer in Terminen gespeichert werden
    teacher_event_group = models.ForeignKey(TeacherEventGroup, on_delete=models.CASCADE)

    parent = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        limit_choices_to={"role": 0},
        default=None,
        null=True,
        blank=True,
        related_name="%(class)s_parent",
    )  # limit_choices_to={'role': 0} besagt, dass nur Nutzer, wo der Wert role glwich 0 ist eingesetzt werden können, also es wird verhindert, dass Lehrer oder andere als Eltern in Terminen gespeichert werden

    student = models.ManyToManyField(Student, default=None, blank=True)

    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(default=timezone.now)

    status = models.IntegerField(choices=EventStatusChoices, default=0)

    occupied = models.BooleanField(default=False)

    objects = EventManager()

    def update_event_lead_status(self, automatic=True, force=False):
        if automatic and self.disable_automatic_changes and not force:
            pass
        else:
            if timezone.now() >= self.end:
                self.lead_status = LeadStatusChoices.NOBODY
                self.lead_manual_override = True
                self.disable_automatic_changes = True
                self.save()
            elif (
                self.teacher_event_group.lead_status_last_change
                >= self.lead_status_last_change
                and (
                    not self.lead_manual_override
                    or (self.lead_manual_override and force)
                )
            ):
                self.lead_status = self.teacher_event_group.lead_status
                self.lead_status_last_change = timezone.now()

                self.save()

    def cancel(self, reopen=True):
        self.active = False
        self.status = EventStatusChoices.CANCELED
        self.save()

        if reopen:
            new_event = Event.objects.create(
                base_event=self.base_event,
                day_group=self.day_group,
                teacher=self.teacher,
                teacher_event_group=self.teacher_event_group,
                start=self.start,
                end=self.end,
                lead_status=self.lead_status,
                lead_manual_override=self.lead_manual_override,
                disable_automatic_changes=self.disable_automatic_changes,
                lead_status_last_change=self.lead_status_last_change,
            )
            new_event.save()

    def get_base_event(self):
        return self.teacher_event_group.day_group.base_event

    # def bulk_create(
    #     teacher: CustomUser,
    #     start: timezone,
    #     end: timezone,
    #     duration: timezone.timedelta,
    #     bulk_mode=True,
    #     ignore_collisions=True,
    # ):
    #     delta = end - start
    #     duration = SiteSettings.objects.all().first().event_duration
    #     total_count = int(delta / duration)

    #     bulk_time_slots_start = [
    #         start + duration * slot_num for slot_num in range(total_count)
    #     ]
    #     bulk_time_slots_end = bulk_time_slots_start.copy()
    #     bulk_time_slots_end.pop(0)
    #     bulk_time_slots_end.append(bulk_time_slots_end[-1] + duration)

    #     collision_events = Event.objects.filter(
    #         Q(teacher=teacher),
    #         Q(start__in=bulk_time_slots_start) | Q(end__in=bulk_time_slots_end),
    #         Q(active=True),
    #     )
    #     # print(collision_events)
    #     if collision_events.exists() and not ignore_collisions:
    #         raise ValueError(
    #             "There is a collision with an already existing, active event. Can´t proceed."
    #         )
    #     elif collision_events.exists():
    #         bulk_time_slots = [
    #             slot
    #             for slot in bulk_time_slots_start
    #             if not slot in list(collision_events.values_list("start", flat=True))
    #             or not slot + duration
    #             in list(collision_events.values_list("end", flat=True))
    #         ]
    #         # print([i for i in bulk_time_slots_start if not i in bulk_time_slots])
    #     else:
    #         bulk_time_slots = bulk_time_slots_start

    #     slot_objects = [
    #         Event(teacher=teacher, start=time_slot, end=time_slot + duration)
    #         for time_slot in bulk_time_slots
    #     ]
    #     if bulk_mode:
    #         events = Event.objects.bulk_create(slot_objects)
    #     else:  # needs much more time as pre_save and post_save signals are triggered.
    #         events = []
    #         for event_object in slot_objects:
    #             event = event_object
    #             event.save()
    #             events.append(event)
    #     return events

    def __str__(self):
        return (
            _("Appointment from ")
            + f"{self.teacher}"
            + _(" on ")
            + f"{self.start.date()}"
            + _(" from ")
            + f"{self.start.time()}"
            + _(" to ")
            + f"{self.end.time()}"
        )
        # return f"Termin von {self.teacher} am {self.start.date()} von {self.start.time()} bis {self.end.time()}"

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        permissions = [
            (
                "condition_prebook_event",
                _(
                    "The user is allowed to book an event before the official booking period because he has an e.g. medical condition."
                ),  # Dieser User darf aus z.B. medizinischen Gründen einen Termin vor der offiziellen Buchungsphasen anfragen.
            ),
            (
                "book_double_event",
                _(
                    "The user is allowed to book a double event with all teachers because of an medical condition."
                ),  # Dieser User darf aus z.B. medizinischen Gründen auch Doppeltermine bei einer Lehrkraft anfragen.
            ),  #! Aktuell nicht in Benutzung
        ]

        rules_permissions = {
            "book_event": user_can_book_event,
            "edit": can_edit_event,
        }


# class Announcements(models.Model):
#     class AnnouncementTypeChoices(models.IntegerChoices):
#         BOOKINK_INQUIRY = 0, _("New booking inquiry")
#         APPOINTEMENT_CANCELLATION = 1, _("Appointment cancellation")
#         SYSTEM_NOTIFICATION = 2, _("System notification")

#     announcement_type = models.IntegerField(
#         choices=AnnouncementTypeChoices, default=AnnouncementTypeChoices.BOOKINK_INQUIRY
#     )
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
#     message = models.TextField(null=True, blank=True)
#     action_link = models.TextField(null=True, blank=True)
#     action_name = models.CharField(max_length=200, null=True, blank=True)

#     read = models.BooleanField(default=False)

#     created = models.DateTimeField(default=timezone.now)

#     def encodedID(self):
#         return urlsafe_base64_encode(force_bytes(self.id))

#     class Meta:
#         verbose_name = _("Notification")
#         verbose_name_plural = _("Notifications")


# class EventLogsMainAttributes(models.Model):
#     log_type = models.IntegerField(
#         choices=EventLogsTypeChoices, default=EventLogsTypeChoices.UPDATED
#     )
#     created = models.DateTimeField(auto_now_add=True, editable=False)

#     class Meta:
#         abstract = True


# class EventChangeLogs(EventLogsMainAttributes):
#     changed_event = models.ForeignKey(Event, on_delete=models.CASCADE)
#     change_action = models.IntegerField(
#         choices=EventLogsActionsCoices, default=EventLogsActionsCoices.CHANGE
#     )
