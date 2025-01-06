from .models import Event, Inquiry
from authentication.models import CustomUser
from django.utils import timezone
from dashboard.models import SiteSettings
from .choices import *
from django.db.models import Q


def check_time_conflict(
    start: timezone.datetime, end: timezone.datetime, parent: CustomUser
) -> bool:
    """Check if there is a time vonflict with an booked event at the same time

    Args:
        start (timezone): The start time of the slot it should be looked for a time conflict
        end (timezone): _description_
        parent (CustomUser): The user

    Returns:
        bool: returns True if a time conflict and false if there is no time conflict.
    """
    events_in_time = (
        Event.objects.filter(Q(parent=parent))
        .exclude(end__lte=start)
        .exclude(start__gte=end)
    )

    return events_in_time.exists()


def check_follow_up_event_exists(
    start: timezone.datetime, end: timezone.datetime, parent: CustomUser
) -> bool:
    min_event_seperation = SiteSettings.objects.first().min_event_seperation
    events_in_time = (
        Event.objects.filter(Q(parent=parent))
        .exclude(start__gt=end + min_event_seperation)
        .exclude(end__lt=start - min_event_seperation)
    )

    return events_in_time.exists()


def check_time_conflict_follow_up(
    start: timezone.datetime, end: timezone.datetime, parent: CustomUser
) -> bool:
    if check_time_conflict(start, end, parent):
        return True

    follow_up_event_bookable = SiteSettings.objects.first().event_in_seperation_bookable

    return (
        check_follow_up_event_exists(start, end, parent)
        and not follow_up_event_bookable
    )


def check_parent_can_book_event(event: Event, parent: CustomUser) -> bool:
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
    match event.lead_status:
        case LeadStatusChoices.ALL:
            return True
        case LeadStatusChoices.INQUIRY:
            if Inquiry.objects.filter(
                Q(requester=event.teacher),
                Q(respondent=parent),
                Q(processed=False),
                Q(base_event=event.get_base_event()),
            ).exists():
                return True
        case LeadStatusChoices.CONDITION:
            if parent.has_perm("dashboard.condition_prebook_event"):
                return True
        case _:
            return False
    return False


def get_parent_event_individual_status(event: Event, parent: CustomUser):
    match event.status:
        case EventStatusChoices.OCCUPIED:
            if event.parent == parent:
                return True, PersonalEventStatusChoices.BOOKED
            else:
                return False, PersonalEventStatusChoices.OCCUPIED
        case EventStatusChoices.INQUIRY:
            if event.parent == parent:
                return True, PersonalEventStatusChoices.INQUIRY_PENDING
            else:
                return False, PersonalEventStatusChoices.OCCUPIED
        case EventStatusChoices.UNOCCUPIED:
            if not event.check_parent_can_book_event(parent):
                return False, PersonalEventStatusChoices.BLOCKED
            if check_time_conflict(event.start, event.end, parent):
                return False, PersonalEventStatusChoices.TIME_CONFLICT
            elif check_time_conflict_follow_up(event.start, event.end, parent):
                return False, PersonalEventStatusChoices.TIME_CONFLICT
            elif check_follow_up_event_exists(event.start, event.end, parent):
                return (
                    True,
                    PersonalEventStatusChoices.TIME_CONFLICT_FOLLOWUP,
                )
            else:
                return True, PersonalEventStatusChoices.EVENT_BOOKABLE
