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

from .choices import *
from .rules import *
from .helpers import (
    check_time_conflict,
    check_follow_up_event_exists,
    check_time_conflict_follow_up,
)

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


class Event(EventMainAttributes):
    base_event = models.ForeignKey(BaseEventGroup, on_delete=models.CASCADE, null=True)
    day_group = models.ForeignKey(DayEventGroup, on_delete=models.CASCADE, null=True)
    teacher = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, limit_choices_to={"role": 1}
    )  # limit_choices_to={'role': 1} besagt, dass nur Nutzer, wo der Wert role glwich 1 ist eingesetzt werden können, also es wird verhindert, dass Eltern oder andere als Lehrer in Terminen gespeichert werden
    teacher_event_group = models.ForeignKey(
        TeacherEventGroup, on_delete=models.CASCADE, null=True
    )

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

    def check_parent_can_book_event(self, parent: CustomUser) -> bool:
        """This function is designed to check if a specified parent user account is allowed to book the specific event.

        Args:
            parent (CustomUser): Pass in the parent

        Returns:
            bool: Describes wether or not the parent is able to book this specific event
        """
        if parent.role != 0:
            raise ValueError(
                _("This user is not a parent.")
            )  # The specified user is not a parent.
        match self.lead_status:
            case LeadStatusChoices.ALL:
                return True
            case LeadStatusChoices.INQUIRY:
                if Inquiry.objects.filter(
                    Q(requester=self.teacher),
                    Q(respondent=parent),
                    Q(processed=False),
                    Q(base_event=self.get_base_event()),
                ).exists():
                    return True
            case LeadStatusChoices.CONDITION:
                if parent.has_perm("dashboard.condition_prebook_event"):
                    return True
            case _:
                return False
        return False

    def get_parent_event_individual_status(self, parent: CustomUser):
        match self.status:
            case EventStatusChoices.OCCUPIED:
                if self.parent == parent:
                    return True, PersonalEventStatusChoices.BOOKED
                else:
                    return False, PersonalEventStatusChoices.OCCUPIED
            case EventStatusChoices.INQUIRY:
                if self.parent == parent:
                    return True, PersonalEventStatusChoices.INQUIRY_PENDING
                else:
                    return False, PersonalEventStatusChoices.OCCUPIED
            case EventStatusChoices.UNOCCUPIED:
                if not self.check_parent_can_book_event(parent):
                    return False, PersonalEventStatusChoices.BLOCKED
                if check_time_conflict(self.start, self.end, parent):
                    return False, PersonalEventStatusChoices.TIME_CONFLICT
                elif check_time_conflict_follow_up(self.start, self.end, parent):
                    return False, PersonalEventStatusChoices.TIME_CONFLICT
                elif check_follow_up_event_exists(self.start, self.end, parent):
                    return (
                        True,
                        PersonalEventStatusChoices.TIME_CONFLICT_FOLLOWUP,
                    )
                else:
                    return True, PersonalEventStatusChoices.EVENT_BOOKABLE

    def get_base_event(self):
        return self.teacher_event_group.day_group.base_event

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


class Inquiry(models.Model):
    class InquiryTypeChoices(models.IntegerChoices):
        TEACHER_REQUEST = 0, _("Inquiry to book an appointment (teacher->parents)")
        APPOINTEMENT_REQUEST = 1, _(
            "Request for confirmation of an appointment (parent->teacher)"
        )

    base_event = models.ForeignKey(BaseEventGroup, on_delete=models.CASCADE, null=True)
    type = models.IntegerField(
        choices=InquiryTypeChoices, default=InquiryTypeChoices.TEACHER_REQUEST
    )
    requester = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="%(class)s_requester"
    )
    students = models.ManyToManyField(Student)
    respondent = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        related_name="%(class)s_respondent",
    )
    reason = models.TextField()

    processed = models.BooleanField(default=False)
    event = models.ForeignKey(
        Event, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )

    class InquiryReactionChoices(models.IntegerChoices):
        NO_RESPONSE = 0, _("No response")
        ACCEPTED = 1, _("Inquiry accepted")
        DECLINED = 3, _("Inquiry declined")

    respondent_reaction = models.IntegerField(
        choices=InquiryReactionChoices, default=InquiryReactionChoices.NO_RESPONSE
    )
    notified = models.BooleanField(default=False)
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = _("Inquiry")
        verbose_name_plural = _("Inquries")


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

    created_at = models.DateTimeField(auto_now_add=True, editable=False)

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


class EventLogsMainAttributes(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        abstract = True


class EventChangeLogs(EventLogsMainAttributes):
    changed_event = models.ForeignKey(Event, on_delete=models.CASCADE)
    changed_teacher_event_group = models.ForeignKey(
        TeacherEventGroup, on_delete=models.CASCADE, null=True, blank=True
    )
    changes_day_event_group = models.ForeignKey(
        DayEventGroup, on_delete=models.CASCADE, null=True, blank=True
    )
