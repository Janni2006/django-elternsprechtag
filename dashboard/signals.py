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
from .utils import check_inquiry_reopen

from events.choices import (
    EventStatusChoices,
    EventFormularStatusChoices,
    EventFormularTypeChoices,
)


@receiver(post_save, sender=Inquiry)
def addAnnouncements(sender, instance: Inquiry, **kwargs):
    """_summary_

    Args:
        sender (_type_): _description_
        instance (Inquiry): _description_
        created (bool): _description_
    """
    if not instance.notified:
        if instance.type == 1:

            email_subject = "New appointment request"
            email_str_body = render_to_string(
                "dashboard/email/new_inquiry/new_inquiry_teacher.txt",
                {
                    "parent": instance.requester,
                    "teacher": instance.respondent,
                    "url": str(os.environ.get("PUBLIC_URL"))
                    + reverse("teacher_event_view", args=[instance.event.id]),
                    # "students": "\n,".join(
                    #    [
                    #        "{} {}".format(student.first_name, student.last_name)
                    #        for student in instance.students.all()
                    #    ]
                    # ),
                },
            )
            email_html_body = render_to_string(
                "dashboard/email/new_inquiry/new_inquiry_teacher.html",
                {
                    "parent": instance.requester,
                    "teacher": instance.respondent,
                    "url": str(os.environ.get("PUBLIC_URL"))
                    + reverse("teacher_event_view", args=[instance.event.id]),
                    "date": datetime.datetime.now().strftime("%d.%m.%Y"),
                    # "students": "\n,".join(
                    #    [
                    #        "{} {}".format(student.first_name, student.last_name)
                    #        for student in instance.students.all()
                    #    ]
                    # ),
                },
            )  #! Dies wird derzeit nicht benutzt

            # async_send_mail.delay(
            #     email_subject,
            #     email_str_body,
            #     instance.respondent.email,
            #     email_html_body=email_html_body,
            # )

            async_send_mail.delay(
                email_subject,
                email_str_body,
                instance.respondent.email,
            )  #! Hier wird keine HTML versendet

            Announcements.objects.create(
                user=instance.respondent,
                message="%s bittet um den Termin am %s um %s Uhr. Bitte bestätigen Sie den Termin."
                % (
                    instance.requester,
                    timezone.localtime(instance.event.start)
                    .date()
                    .strftime("%d.%m.%Y"),
                    timezone.localtime(instance.event.start).time().strftime("%H:%M"),
                ),
            )
            instance.notified = True
            instance.save()
        elif instance.type == 0 and len(instance.students.all()) > 0:
            instance.notified = True
            instance.save()

            email_subject = "New appointment request"
            email_str_body = render_to_string(
                "dashboard/email/new_inquiry/new_inquiry_parent.txt",
                {
                    "parent": instance.respondent,
                    "teacher": instance.requester,
                    "url": str(os.environ.get("PUBLIC_URL"))
                    + reverse(
                        "inquiry_detail_view",
                        args=[urlsafe_base64_encode(force_bytes(instance.id))],
                    ),
                    # "students": "\n,".join(
                    #    [
                    #        "{} {}".format(student.first_name, student.last_name)
                    #        for student in instance.students.all()
                    #    ]
                    # ),
                },
            )
            email_html_body = render_to_string(
                "dashboard/email/new_inquiry/new_inquiry_parent.html",
                {
                    "parent": instance.respondent,
                    "teacher": instance.requester,
                    "url": str(os.environ.get("PUBLIC_URL"))
                    + reverse(
                        "inquiry_detail_view",
                        args=[urlsafe_base64_encode(force_bytes(instance.id))],
                    ),
                    "date": datetime.datetime.now().strftime("%d.%m.%Y"),
                    # "students": "\n,".join(
                    #    [
                    #        "{} {}".format(student.first_name, student.last_name)
                    #        for student in instance.students.all()
                    #    ]
                    # ),
                },
            )  #! Dies wird derzeit nicht benutzt

            # async_send_mail.delay(
            #     email_subject,
            #     email_str_body,
            #     instance.respondent.email,
            #     email_html_body=email_html_body,
            # )

            async_send_mail.delay(
                email_subject,
                email_str_body,
                instance.respondent.email,
            )  #! Hier wird keine HTML versendet

            Announcements.objects.create(
                user=instance.respondent,
                message="%s bittet Sie darum einen Termin zu erstellen"
                % (instance.requester),
            )


# @receiver(pre_save, sender=EventChangeFormula)
# def openNewEventChangeFormulaOnDisapprove(sender, instance, *args, **kwargs):
#     if instance.id is None:
#         pass
#     else:
#         current = instance
#         previouse = EventChangeFormula.objects.get(id=instance.id)

#         if (
#             previouse.status == EventFormularStatusChoices.PENDING_CONFIRMATION
#             and current.status == EventFormularStatusChoices.DECLINED
#             and current.type == EventFormularTypeChoices.TIME_PERIODS
#         ):
#             EventChangeFormula.objects.create(
#                 teacher=instance.teacher,
#                 date=instance.date,
#                 teacher_event_group=instance.teacher_event_group,
#                 day_group=instance.day_group,
#             )

#             previouse.childformular.all().update(
#                 status=EventFormularStatusChoices.DECLINED
#             )


# @receiver(pre_save, sender=EventChangeFormula)
# def apply_break_formulars(sender, instance, *args, **kwargs):
#     if instance.id is None:
#         pass
#     else:
#         current = instance
#         previouse = EventChangeFormula.objects.get(id=instance.id)

#         if (
#             previouse.status == EventFormularStatusChoices.PENDING_CONFIRMATION
#             and current.status == EventFormularStatusChoices.APPROVED
#             and current.type == EventFormularTypeChoices.BREAKS
#         ):
#             events = Event.objects.filter(
#                 Q(teacher_event_group=previouse.teacher_event_group),
#                 Q(
#                     start__gte=timezone.datetime.combine(
#                         previouse.date, previouse.start_time
#                     )
#                 ),
#                 Q(
#                     end__lte=timezone.datetime.combine(
#                         previouse.date, previouse.end_time
#                     )
#                 ),
#                 Q(status=EventStatusChoices.UNOCCUPIED),
#             )

#             events.update(
#                 lead_status=LeadStatusChoices.NOBODY,
#                 lead_manual_override=True,
#                 disable_automatic_changes=True,
#                 lead_status_last_change=timezone.now(),
#             )


# @receiver(pre_save, sender=EventChangeFormula)
# def apply_sick_leave_formulars(sender, instance, *args, **kwargs):
#     if instance.id is None:
#         pass
#     else:
#         current = instance
#         previouse = EventChangeFormula.objects.get(id=instance.id)

#         if (
#             previouse.status == EventFormularStatusChoices.PENDING_CONFIRMATION
#             and current.status == EventFormularStatusChoices.APPROVED
#             and current.type == EventFormularTypeChoices.ILLNESS
#         ):
#             if current.no_events:
#                 events = Event.objects.filter(
#                     Q(teacher_event_group=previouse.teacher_event_group),
#                     Q(start__gte=timezone.now()),
#                 )
#             else:
#                 events = Event.objects.filter(
#                     Q(teacher_event_group=previouse.teacher_event_group),
#                     Q(
#                         start__gte=timezone.datetime.combine(
#                             previouse.date, previouse.start_time
#                         )
#                     ),
#                     Q(
#                         end__lte=timezone.datetime.combine(
#                             previouse.date, previouse.end_time
#                         )
#                     ),
#                     Q(start__gte=timezone.now()),
#                 )

#             # Block events ==> No one should be able to book these events from now on
#             events.update(
#                 lead_status=LeadStatusChoices.NOBODY,
#                 lead_manual_override=True,
#                 disable_automatic_changes=True,
#                 lead_status_last_change=timezone.now(),
#             )

#             booked_events = events.exclude(status=EventStatusChoices.UNOCCUPIED)

#             parents = list(set(list(booked_events.values_list("parent", flat=True))))

#             for parent in parents:
#                 if parent != None:
#                     parent_obj = CustomUser.objects.get(pk=parent)
#                     parent_events = booked_events.filter(parent=parent)

#                     email_str_body = render_to_string(
#                         "dashboard/email/teacher_sick_leave/teacher_sick_leave.txt",
#                         {
#                             "parent": parent_obj,
#                             "teacher": current.teacher_event_group.teacher,
#                             "events": parent_events,
#                         },
#                     )

#                     async_send_mail.delay(
#                         email_subject=f"Krankschreibung von {current.teacher_event_group.teacher.first_name} {current.teacher_event_group.teacher.last_name}",
#                         email_body=email_str_body,
#                         email_receiver=parent_obj.email,
#                     )

#             for event in booked_events:
#                 event.student.clear()

#                 event.status = EventStatusChoices.UNOCCUPIED
#                 event.parent = None
#                 event.occupied = False

#                 event.save()


# @receiver(pre_save, sender=Event)
# def checkLeadStatusChange(sender, instance, *args, **kwargs):
#     current = instance
#     try:
#         previouse = Event.objects.get(id=instance.id)
#     except Event.DoesNotExist:
#         pass
#     else:
#         if current.lead_status != previouse.lead_status:
#             instance.lead_status_last_change = timezone.now()


# @receiver(post_save, sender=DayEventGroup)
# def updateBaseEventValidUntil(
#     sender, instance: DayEventGroup, created, *args, **kwargs
# ):
#     if created:
#         # if (
#         #     not DayEventGroup.objects.filter(
#         #         Q(date__gte=instance.date), Q(base_event=instance.base_event)
#         #     )
#         #     .exclude(pk=instance.pk)
#         #     .exists()
#         #     and instance.base_event.valid_until < instance.date
#         # ):
#         #     instance.base_event.valid_until = instance.date + timezone.timedelta(days=7)
#         #     instance.base_event.save()
#         print(instance.base_event)
#         newest = (
#             DayEventGroup.objects.filter(base_event=instance.base_event)
#             .order_by("date")
#             .last()
#         )
#         print(newest)
#         instance.base_event.valid_until = newest.date + timezone.timedelta(days=7)
#         instance.base_event.save()


# @receiver(pre_save, sender=BaseEventGroup)
# def updateLeadDatesBaseEvent(sender, instance, *args, **kwargs):
#     current: BaseEventGroup = instance
#     try:
#         previouse = BaseEventGroup.objects.get(id=current.id)
#     except BaseEventGroup.DoesNotExist:
#         pass
#     else:
#         day_event_groups = DayEventGroup.objects.filter(Q(base_event=previouse))

#         if not current.force:
#             day_event_groups = day_event_groups.exclude(Q(lead_manual_override=True))
#         elif current.force and not current.manual_apply:
#             current.force = False
#             current.save()
#         if current.manual_apply:
#             for day_event_group in day_event_groups:
#                 day_event_group.lead_start = instance.lead_start
#                 day_event_group.lead_inquiry_start = instance.lead_inquiry_start
#                 day_event_group.lead_status = current.lead_status
#                 day_event_group.manual_apply = True
#                 day_event_group.force = current.force
#                 day_event_group.disable_automatic_changes = (
#                     current.disable_automatic_changes
#                 )
#                 day_event_group.save()

#             current.manual_apply = False
#             current.force = False
#             current.save()


# @receiver(pre_save, sender=DayEventGroup)
# def updateLeadDatesDayEventGroups(sender, instance, *args, **kwargs):
#     current: DayEventGroup = instance
#     try:
#         previouse = DayEventGroup.objects.get(id=current.id)
#     except DayEventGroup.DoesNotExist:
#         pass
#     else:
#         teacher_event_groups = TeacherEventGroup.objects.filter(Q(day_group=previouse))
#         if not current.force:
#             teacher_event_groups = teacher_event_groups.exclude(
#                 Q(lead_manual_override=True)
#             )
#         elif current.force and not current.manual_apply:
#             current.force = False
#             current.save()

#         if current.manual_apply:
#             for teacher_event_group in teacher_event_groups:
#                 teacher_event_group.lead_start = instance.lead_start
#                 teacher_event_group.lead_inquiry_start = instance.lead_inquiry_start
#                 teacher_event_group.lead_status = current.lead_status
#                 teacher_event_group.manual_apply = True
#                 teacher_event_group.disable_automatic_changes = (
#                     current.disable_automatic_changes
#                 )
#                 teacher_event_group.force = current.force
#                 teacher_event_group.lead_manual_override = False
#                 teacher_event_group.save()

#             current.manual_apply = False
#             current.force = False
#             current.save()


# @receiver(pre_save, sender=TeacherEventGroup)
# def updateLeadStatusPerEvent(sender, instance, *args, **kwargs):
#     current: TeacherEventGroup = instance
#     try:
#         previouse = TeacherEventGroup.objects.get(id=current.id)
#     except TeacherEventGroup.DoesNotExist:
#         pass
#     else:
#         events = Event.objects.filter(Q(teacher_event_group=previouse))
#         if not current.force:
#             events = events.exclude(Q(lead_manual_override=True))
#         elif current.force and not current.manual_apply:
#             current.force = False
#             current.save()

#         if current.manual_apply:
#             events.update(
#                 lead_status=current.lead_status,
#                 disable_automatic_changes=current.disable_automatic_changes,
#                 lead_manual_override=False,
#             )

#             current.manual_apply = False
#             current.force = False
#             current.save()
