from .models import *
from authentication.models import CustomUser
from django.utils import timezone


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
