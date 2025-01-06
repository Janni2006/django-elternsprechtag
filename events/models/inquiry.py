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

from ..choices import *
from ..rules import *

from rules.contrib.models import RulesModel

from .event import BaseEventGroup, Event


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
