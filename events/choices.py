from django.db import models
from django.utils.translation import gettext as _


class LeadStatusChoices(models.IntegerChoices):
    NOBODY = 0, _("Nobody can currently request this appointment.")
    CONDITION = 1, _(
        "Only parents with special authorisations can currently request this appointment."
    )
    INQUIRY = 2, _(
        "Only parents who have received a request from the teacher can currently request this appointment."
    )
    ALL = 3, _("All parents can request this appointment at the moment.")


class EventStatusChoices(models.IntegerChoices):
    UNOCCUPIED = 0, _("Unoccupied")
    OCCUPIED = 1, _("Occupied")
    INQUIRY = 2, _("Inquiry pending")
    CANCELED = 3, _("Canceles")


class EventFormularStatusChoices(models.IntegerChoices):
    PENDING_PROCESSING = 0, _("Wait for processing")
    PENDING_CONFIRMATION = 1, _("Wait for confirmation")
    APPROVED = 2, _("Approved")
    DECLINED = 3, _("Declined")
    REMOVED = 4, _("Removed")


class PersonalEventStatusChoices:
    EVENT_BOOKABLE = 0, _("Event bookable")
    INQUIRY_PENDING = 1, _("Inquiry pending")
    BOOKED = 2, _("Booked")
    OCCUPIED = 3, _("Occupied")
    BLOCKED = 4, _("Blocked")
    TIME_CONFLICT = 5, _("Time conflict")
    TIME_CONFLICT_FOLLOWUP = 6, _("Followup event")
