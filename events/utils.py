from events.models.event import Event, DayEventGroup
from events.models.inquiry import Inquiry
from .choices import *
from django.db.models import Q
from django.utils import timezone


from authentication.models import CustomUser
from dashboard.models import SiteSettings


# def cancel_event(event: Event, reopen=True):
#     event.active = False
#     event.status = EventStatusChoices.CANCELED
#     event.save()

#     if reopen:
#         new_event = Event.objects.create(
#             base_event=event.base_event,
#             day_group=event.day_group,
#             teacher=event.teacher,
#             teacher_event_group=event.teacher_event_group,
#             start=event.start,
#             end=event.end,
#             lead_status=event.lead_status,
#             lead_manual_override=event.lead_manual_override,
#             disable_automatic_changes=event.disable_automatic_changes,
#             lead_status_last_change=event.lead_status_last_change,
#         )
#         new_event.save()


def check_inquiry_reopen(parent: CustomUser, teacher: CustomUser):
    for inquiry in Inquiry.objects.filter(
        Q(respondent=parent), Q(requester=teacher), Q(type=0), Q(processed=True)
    ):
        print(
            inquiry.students.all(),
            Event.objects.filter(
                Q(teacher=teacher), Q(parent=parent), Q(occupied=True)
            ).values_list("student", flat=True),
        )
        day_group = DayEventGroup.objects.filter(base_event=inquiry.base_event)
        for student in inquiry.students.all():
            if student.pk not in Event.objects.filter(
                Q(teacher=teacher),
                Q(parent=parent),
                Q(occupied=True),
                Q(day_group__in=day_group),
            ).values_list("student", flat=True):
                inquiry.processed = False
                inquiry.event = None
                inquiry.save()
