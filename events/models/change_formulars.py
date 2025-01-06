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

from .event import Event, BaseEventGroup, DayEventGroup, TeacherEventGroup

from ..choices import *
from ..rules import *

from rules.contrib.models import RulesModel


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


class EventChangeFormula(models.Model):
    """
    Dieses Model dient dazu, jedem Lehrer die Möglichkeit zu geben, seine Zeiten für den Elternsprtechtag selber einzurrichten. In Zukunft können hier auch Anträge auf die Blockierung einzelner Termine eingereicht werden.
    """

    # id = models.UUIDField(unique=True, default=uuid.uuid4, primary_key=True)

    type = models.IntegerField(
        choices=EventFormularTypeChoices, default=EventFormularTypeChoices.TIME_PERIODS
    )
    connected_events = models.ManyToManyField(Event, blank=True)
    parent_formular = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="childformular",
    )
    day_group = models.ForeignKey(
        DayEventGroup, on_delete=models.CASCADE, null=True, blank=True
    )
    teacher_event_group = models.ForeignKey(
        TeacherEventGroup, on_delete=models.CASCADE, null=True, blank=True
    )
    teacher = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={"role": 1},
        blank=False,
        verbose_name=_("Teacher"),
    )
    start_time = models.TimeField(blank=True, null=True, verbose_name=_("Start time"))
    end_time = models.TimeField(blank=True, null=True, verbose_name=_("End time"))

    no_events = models.BooleanField(default=False, verbose_name=_("No events"))

    status = models.IntegerField(
        choices=EventFormularStatusChoices,
        default=EventFormularStatusChoices.PENDING_PROCESSING,
    )

    reversable = models.BooleanField(default=False)
    applied = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def approve(self):
        if not self.status == EventFormularStatusChoices.PENDING_CONFIRMATION:
            raise ValueError("The status of the formular does not allow for approval.")

        self.status = EventFormularStatusChoices.APPROVED
        self.save()

    def disapprove(self):
        if not self.status == EventFormularStatusChoices.PENDING_CONFIRMATION:
            raise ValueError(
                "The status of the formular does not allow for disapproval."
            )

        self.status = EventFormularStatusChoices.DECLINED
        self.save()

    def apply(self):
        if self.status != EventFormularStatusChoices.APPROVED:
            raise ValueError("Only approved formulars can be applied!")
        if self.applied:
            raise ValueError(
                "It is prohibited to re-apply an already applied formular. "
            )

        match self.type:
            case EventFormularTypeChoices.TIME_PERIODS:
                if not self.no_events:
                    # async_create_events_special.delay(
                    #     [self.teacher.id],
                    #     self.date.strftime("%Y-%m-%d"),
                    #     self.start_time.strftime("%H:%M:%S"),
                    #     self.end_time.strftime("%H:%M:%S"),
                    # )
                    date = self.day_group.date
                    teacher = self.teacher_event_group.teacher
                    start = timezone.datetime.combine(
                        date,
                        self.start_time,
                    )
                    end = timezone.datetime.combine(
                        date,
                        self.end_time,
                    )
                    duration = SiteSettings.objects.all().first().event_duration

                    events = Event.bulk_create(teacher, start, end, duration)

                    self.connected_events.set(events)
                    self.applied = True
                    self.save()
            case EventFormularTypeChoices.ILLNESS:
                events = Event.objects.filter(
                    Q(teacher_event_group=self.teacher_event_group),
                    Q(start__gte=self.start_time),
                    Q(end__lte=self.end_time),
                    Q(active=True),
                )

                booked_events = events.filter(
                    Q(status=EventStatusChoices.INQUIRY)
                    | Q(status=EventStatusChoices.OCCUPIED),
                )

                for event in booked_events:
                    pass  # TODO: Implement event cancellation!

                empty_events = events.filter(Q(status=EventStatusChoices.UNOCCUPIED))

                empty_events.update(
                    lead_status=LeadStatusChoices.NOBODY,
                    lead_manual_override=True,
                    disable_automatic_changes=True,
                    active=False,
                    updated=timezone.now(),
                )

                self.connected_events.set(events)
                self.applied = True
                self.save()

    class Meta:
        verbose_name = _("Event creation formula")
        verbose_name_plural = _("Event creation formulas")
        permissions = [
            (
                "approve_disapprove",
                _(
                    "Can accept or reject submitted time periods for other users."
                ),  # Can approve/disapprove the formulars for other users
            )
        ]


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
