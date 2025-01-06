from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from events.models import (
    Event,
    Inquiry,
    EventChangeFormula,
    DayEventGroup,
    TeacherEventGroup,
    BaseEventGroup,
)
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


@receiver(pre_save, sender=Event)
def checkLeadStatusChange(sender, instance, *args, **kwargs):
    current = instance
    try:
        previouse = Event.objects.get(id=instance.id)
    except Event.DoesNotExist:
        pass
    else:
        if current.lead_status != previouse.lead_status:
            instance.lead_status_last_change = timezone.now()


@receiver(post_save, sender=DayEventGroup)
def updateBaseEventValidUntil(
    sender, instance: DayEventGroup, created, *args, **kwargs
):
    if created:
        # if (
        #     not DayEventGroup.objects.filter(
        #         Q(date__gte=instance.date), Q(base_event=instance.base_event)
        #     )
        #     .exclude(pk=instance.pk)
        #     .exists()
        #     and instance.base_event.valid_until < instance.date
        # ):
        #     instance.base_event.valid_until = instance.date + timezone.timedelta(days=7)
        #     instance.base_event.save()
        print(instance.base_event)
        newest = (
            DayEventGroup.objects.filter(base_event=instance.base_event)
            .order_by("date")
            .last()
        )
        print(newest)
        instance.base_event.valid_until = newest.date + timezone.timedelta(days=7)
        instance.base_event.save()


@receiver(pre_save, sender=BaseEventGroup)
def updateLeadDatesBaseEvent(sender, instance, *args, **kwargs):
    current: BaseEventGroup = instance
    try:
        previouse = BaseEventGroup.objects.get(id=current.id)
    except BaseEventGroup.DoesNotExist:
        pass
    else:
        day_event_groups = DayEventGroup.objects.filter(Q(base_event=previouse))

        if not current.force:
            day_event_groups = day_event_groups.exclude(Q(lead_manual_override=True))
        elif current.force and not current.manual_apply:
            current.force = False
            current.save()
        if current.manual_apply:
            for day_event_group in day_event_groups:
                day_event_group.lead_start = instance.lead_start
                day_event_group.lead_inquiry_start = instance.lead_inquiry_start
                day_event_group.lead_status = current.lead_status
                day_event_group.manual_apply = True
                day_event_group.force = current.force
                day_event_group.disable_automatic_changes = (
                    current.disable_automatic_changes
                )
                day_event_group.save()

            current.manual_apply = False
            current.force = False
            current.save()


@receiver(pre_save, sender=DayEventGroup)
def updateLeadDatesDayEventGroups(sender, instance, *args, **kwargs):
    current: DayEventGroup = instance
    try:
        previouse = DayEventGroup.objects.get(id=current.id)
    except DayEventGroup.DoesNotExist:
        pass
    else:
        teacher_event_groups = TeacherEventGroup.objects.filter(Q(day_group=previouse))
        if not current.force:
            teacher_event_groups = teacher_event_groups.exclude(
                Q(lead_manual_override=True)
            )
        elif current.force and not current.manual_apply:
            current.force = False
            current.save()

        if current.manual_apply:
            for teacher_event_group in teacher_event_groups:
                teacher_event_group.lead_start = instance.lead_start
                teacher_event_group.lead_inquiry_start = instance.lead_inquiry_start
                teacher_event_group.lead_status = current.lead_status
                teacher_event_group.manual_apply = True
                teacher_event_group.disable_automatic_changes = (
                    current.disable_automatic_changes
                )
                teacher_event_group.force = current.force
                teacher_event_group.lead_manual_override = False
                teacher_event_group.save()

            current.manual_apply = False
            current.force = False
            current.save()


@receiver(pre_save, sender=TeacherEventGroup)
def updateLeadStatusPerEvent(sender, instance, *args, **kwargs):
    current: TeacherEventGroup = instance
    try:
        previouse = TeacherEventGroup.objects.get(id=current.id)
    except TeacherEventGroup.DoesNotExist:
        pass
    else:
        events = Event.objects.filter(Q(teacher_event_group=previouse))
        if not current.force:
            events = events.exclude(Q(lead_manual_override=True))
        elif current.force and not current.manual_apply:
            current.force = False
            current.save()

        if current.manual_apply:
            events.update(
                lead_status=current.lead_status,
                disable_automatic_changes=current.disable_automatic_changes,
                lead_manual_override=False,
            )

            current.manual_apply = False
            current.force = False
            current.save()
