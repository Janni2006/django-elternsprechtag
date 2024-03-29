from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Event, Inquiry, Announcements, EventChangeFormula
from django.db.models import Q
from django.utils import timezone
from authentication.tasks import async_send_mail
from django.template.loader import render_to_string
from django.urls import reverse
import os
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from .utils import check_inquiry_reopen


@receiver(post_save, sender=Event)
def handleInquiries(sender, instance, **kwargs):
    """
    Diese Funktion dient dazu nach der Buchung eines Termins mögliche Anfragen Seitens des Lehrers auf beantwortet zu setzen.

    Args:
        sender (_type_): _description_
        instance (Event): _description_
    """
    inquiries = Inquiry.objects.filter(
        Q(type=0),
        Q(requester=instance.teacher),
        Q(respondent=instance.parent),
        Q(event=None),
    )
    for inquiry in inquiries:
        if inquiry.students.first().shield_id in list(
            instance.student.values_list("shield_id", flat=True)
        ):
            inquiry.event = instance
            inquiry.processed = True
            inquiry.save()


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
            async_send_mail.delay(
                "Termin-Anfrage",
                render_to_string(
                    "dashboard/email/new_inquiry_teacher.html",
                    {
                        "parent": instance.requester,
                        "teacher": instance.respondent,
                        "url": reverse("teacher_event_view", args=[instance.event.id]),
                        "current_site": os.environ.get("PUBLIC_URL"),
                    },
                ),
                instance.respondent.email,
            )
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

            async_send_mail.delay(
                "Gesprächsanfrage",
                render_to_string(
                    "dashboard/email/new_inquiry_parent.html",
                    {
                        "parent": instance.respondent,
                        "teacher": instance.requester,
                        "students": "\n,".join(
                            [
                                "{} {}".format(student.first_name, student.last_name)
                                for student in instance.students.all()
                            ]
                        ),
                        "url": reverse(
                            "inquiry_detail_view",
                            args=[urlsafe_base64_encode(force_bytes(instance.id))],
                        ),
                        "current_site": os.environ.get("PUBLIC_URL"),
                    },
                ),
                instance.respondent.email,
            )
            Announcements.objects.create(
                user=instance.respondent,
                message="%s bittet Sie darum einen Termin zu erstellen"
                % (instance.requester),
            )


@receiver(post_delete, sender=Inquiry)
def freeEvents(sender, instance, **kwarg):
    inquiriy = instance
    event = inquiriy.event

    if inquiriy.type == 1 and not inquiriy.processed:
        check_inquiry_reopen(event.parent, event.teacher)
        event.parent = None
        event.student.clear()
        event.status = 0
        event.occupied = False
        event.save()

        print(event)


@receiver(pre_save, sender=EventChangeFormula)
def openNewEventChangeFormulaOnDisapprove(sender, instance, *args, **kwargs):
    if instance.id is None:
        pass
    else:
        current = instance
        previouse = EventChangeFormula.objects.get(id=instance.id)

        if previouse.status == 1 and current.status == 3 and current.type == 0:
            EventChangeFormula.objects.create(
                teacher=instance.teacher, date=instance.date
            )
