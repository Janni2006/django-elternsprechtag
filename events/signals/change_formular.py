from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from events.models import (
    Event,
    Inquiry,
    EventChangeFormula,
    DayEventGroup,
    TeacherEventGroup,
    BaseEventGroup,
    LeadStatusChoices,
)
from dashboard.models import Announcements
from django.db.models import Q
from django.utils import timezone
from authentication.tasks import async_send_mail
from authentication.models import CustomUser
from django.template.loader import render_to_string
from django.urls import reverse
import os
import datetime
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from ..utils import check_inquiry_reopen

from events.choices import (
    EventStatusChoices,
    EventFormularStatusChoices,
    EventFormularTypeChoices,
)


@receiver(pre_save, sender=EventChangeFormula)
def openNewEventChangeFormulaOnDisapprove(sender, instance, *args, **kwargs):
    if instance.id is None:
        pass
    else:
        current = instance
        previouse = EventChangeFormula.objects.get(id=instance.id)

        if (
            previouse.status == EventFormularStatusChoices.PENDING_CONFIRMATION
            and current.status == EventFormularStatusChoices.DECLINED
            and current.type == EventFormularTypeChoices.TIME_PERIODS
        ):
            EventChangeFormula.objects.create(
                teacher=instance.teacher,
                date=instance.date,
                teacher_event_group=instance.teacher_event_group,
                day_group=instance.day_group,
            )

            previouse.childformular.all().update(
                status=EventFormularStatusChoices.DECLINED
            )


@receiver(pre_save, sender=EventChangeFormula)
def apply_break_formulars(sender, instance, *args, **kwargs):
    if instance.id is None:
        pass
    else:
        current = instance
        previouse = EventChangeFormula.objects.get(id=instance.id)

        if (
            previouse.status == EventFormularStatusChoices.PENDING_CONFIRMATION
            and current.status == EventFormularStatusChoices.APPROVED
            and current.type == EventFormularTypeChoices.BREAKS
        ):
            events = Event.objects.filter(
                Q(teacher_event_group=previouse.teacher_event_group),
                Q(
                    start__gte=timezone.datetime.combine(
                        previouse.date, previouse.start_time
                    )
                ),
                Q(
                    end__lte=timezone.datetime.combine(
                        previouse.date, previouse.end_time
                    )
                ),
                Q(status=EventStatusChoices.UNOCCUPIED),
            )

            events.update(
                lead_status=LeadStatusChoices.NOBODY,
                lead_manual_override=True,
                disable_automatic_changes=True,
                lead_status_last_change=timezone.now(),
            )


@receiver(pre_save, sender=EventChangeFormula)
def apply_sick_leave_formulars(sender, instance, *args, **kwargs):
    if instance.id is None:
        pass
    else:
        current = instance
        previouse = EventChangeFormula.objects.get(id=instance.id)

        if (
            previouse.status == EventFormularStatusChoices.PENDING_CONFIRMATION
            and current.status == EventFormularStatusChoices.APPROVED
            and current.type == EventFormularTypeChoices.ILLNESS
        ):
            if current.no_events:
                events = Event.objects.filter(
                    Q(teacher_event_group=previouse.teacher_event_group),
                    Q(start__gte=timezone.now()),
                )
            else:
                events = Event.objects.filter(
                    Q(teacher_event_group=previouse.teacher_event_group),
                    Q(
                        start__gte=timezone.datetime.combine(
                            previouse.date, previouse.start_time
                        )
                    ),
                    Q(
                        end__lte=timezone.datetime.combine(
                            previouse.date, previouse.end_time
                        )
                    ),
                    Q(start__gte=timezone.now()),
                )

            # Block events ==> No one should be able to book these events from now on
            events.update(
                lead_status=LeadStatusChoices.NOBODY,
                lead_manual_override=True,
                disable_automatic_changes=True,
                lead_status_last_change=timezone.now(),
            )

            booked_events = events.exclude(status=EventStatusChoices.UNOCCUPIED)

            parents = list(set(list(booked_events.values_list("parent", flat=True))))

            for parent in parents:
                if parent != None:
                    parent_obj = CustomUser.objects.get(pk=parent)
                    parent_events = booked_events.filter(parent=parent)

                    email_str_body = render_to_string(
                        "dashboard/email/teacher_sick_leave/teacher_sick_leave.txt",
                        {
                            "parent": parent_obj,
                            "teacher": current.teacher_event_group.teacher,
                            "events": parent_events,
                        },
                    )

                    async_send_mail.delay(
                        email_subject=f"Krankschreibung von {current.teacher_event_group.teacher.first_name} {current.teacher_event_group.teacher.last_name}",
                        email_body=email_str_body,
                        email_receiver=parent_obj.email,
                    )

            for event in booked_events:
                event.student.clear()

                event.status = EventStatusChoices.UNOCCUPIED
                event.parent = None
                event.occupied = False

                event.save()
