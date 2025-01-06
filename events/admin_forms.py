from typing import Any
from django import forms
from events.models import (
    Inquiry,
    Event,
    DayEventGroup,
    TeacherEventGroup,
)
from authentication.models import CustomUser, Student
from dashboard.models import SiteSettings
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class AdminEventCreationFormulaForm(forms.Form):
    teacher = forms.ModelMultipleChoiceField(queryset=CustomUser.objects.filter(role=1))
    date = forms.DateField(
        widget=forms.SelectDateWidget(), initial=timezone.datetime.now().date
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.add_input(Submit("submit", _("Save")))


class EventCreationForm(forms.BaseInlineFormSet):
    class Meta:
        model = Event
        fields = ["teacher", "start", "end"]

    teacher = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role=1), required=True
    )
    start = forms.DateTimeField(required=True)
    end = forms.DateTimeField(required=True)
    lead_start = forms.DateField(required=False)
    lead_inquiry_start = forms.DateField(required=False)

    def clean(self) -> dict[str, Any]:
        cleaned_data = super(EventCreationForm, self).clean()
        start = cleaned_data.get("start")
        end = cleaned_data.get("end")
        lead_start = cleaned_data.get("lead_start")
        lead_inquiry_start = cleaned_data.get("lead_inquiry_start")
        if start > end:
            self.add_error("end", _("The end time must be later than the start time."))
        if lead_start > start:
            self.add_error(
                "lead_start",
                _(
                    "The start time of the booking phase must be before the start of the appointments."
                ),
            )
        if lead_start > lead_inquiry_start:
            self.add_error(
                "lead_inquiry_start",
                _(
                    "The starting time of answering enquiries must be before the start time of the booking phase."
                ),
            )
        return cleaned_data

    def save(self):
        teacher = self.cleaned_data["teacher"]
        start = self.cleaned_data["start"]
        end = self.cleaned_data["end"]

        if self.cleaned_data["lead_start"] and self.cleaned_data["lead_inquiry_start"]:
            lead_start = self.cleaned_data["lead_start"]
            lead_inquiry_start = self.cleaned_data["lead_inquiry_start"]
        else:
            lead_start = start.date() - timezone.timedelta(days=7)
            lead_inquiry_start = start.date() - timezone.timedelta(days=14)

        day_group = DayEventGroup.objects.get_or_create(
            Q(date=start.date()),
            Q(lead_start=lead_start),
            Q(lead_inquiry_start=lead_inquiry_start),
        )
        teacher_event_group = TeacherEventGroup.objects.get_or_create(
            Q(teacher=self.cleaned_data["teacher"]),
            Q(day_group=day_group),
            Q(lead_start=lead_start),
            Q(lead_inquiry_start=lead_inquiry_start),
        )
        event = Event.objects.create(
            day_group=day_group,
            teacher_event_group=teacher_event_group,
            teacher=teacher,
            start=start,
            end=end,
        )
        event.save()

        return event
