from typing import Dict
from django.shortcuts import render, redirect
from authentication.models import StudentChange, CustomUser, Upcomming_User
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext as _
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
import os
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from django.contrib.auth.password_validation import password_validators_help_text_html
from django.urls import reverse

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import get_object_or_404

import datetime

from ..forms import *
from ..tasks import *
from ..utils import *
from ..tables import *
from ..filters import *
from ..helpers import *
from django_tables2 import SingleTableView, SingleTableMixin
from django_filters.views import FilterView
from general_tasks.tasks import async_send_mail

from django.contrib.admin.views.decorators import staff_member_required

from dashboard.models import Event, EventChangeFormula
from dashboard.tasks import async_create_events_special, apply_event_change_formular

import csv, io, os

from django.utils.decorators import method_decorator

login_staff = [login_required, staff_member_required]


@method_decorator(login_staff, name="dispatch")
class AdministrativeDashboard(View):
    def get(self, request, *args, **kwargs):
        data = [
            Event.objects.filter(lead_status=0).count(),
            Event.objects.filter(lead_status=1).count(),
            Event.objects.filter(lead_status=2).count(),
            Event.objects.filter(lead_status=3).count(),
        ]
        labels = [
            "Blockiert",
            "Beschränkt auf Berechtigte",
            "Beschränkt auf Anfragen",
            "Offen",
        ]
        base_events_str = ""
        for index, base in enumerate(
            BaseEventGroup.objects.filter(valid_until__gte=timezone.now())
        ):

            base_events_str += str(base)
            if (
                index + 2
                < BaseEventGroup.objects.filter(valid_until__gte=timezone.now()).count()
            ):
                base_events_str += str(", ")
            elif (
                index + 2
                == BaseEventGroup.objects.filter(
                    valid_until__gte=timezone.now()
                ).count()
            ):
                base_events_str += " und "

        if not Student.objects.all().exists():
            with_parent_percent = 0
            without_parent_percent = 0
        else:
            with_parent_percent = int(
                (
                    Student.objects.filter(customuser__isnull=False).count()
                    / Student.objects.all().count()
                )
                * 100
            )
            without_parent_percent = int(
                (
                    Student.objects.filter(customuser__isnull=True).count()
                    / Student.objects.all().count()
                )
                * 100
            )

        context = {
            "students": {
                "total": Student.objects.all().count(),
                "with_parent": Student.objects.filter(customuser__isnull=False).count(),
                "with_parent_percent": with_parent_percent,
                "without_parent": Student.objects.filter(
                    customuser__isnull=True
                ).count(),
                "without_parent_percent": without_parent_percent,
                "unapproved_changes": StudentChange.objects.filter(
                    approved=False
                ).exists(),
                "unsend_up_users": Upcomming_User.objects.filter(
                    email_send=False
                ).exists(),
            },
            "events": {
                "total": Event.objects.all().count(),
                "upcomming": Event.objects.filter(start__gte=timezone.now()).count(),
                "base_events": BaseEventGroup.objects.filter(
                    valid_until__gte=timezone.now()
                ),
                "base_events_str": base_events_str,
                "base_events_table": BaseEventsTable(
                    BaseEventGroup.objects.filter(valid_until__gte=timezone.now())[:5],
                    orderable=False,
                ),
                "change_formular": EventChangeFormularForm(),
                "structure": get_event_creation_modal_context(),
                "change_formular_new": EventAddNewDateForm(),
            },
            "labels": labels,
            "data": data,
            # "page_under_construction": True,
        }
        return render(
            request,
            "administrative/dashboard/administrative_dashboard.html",
            context,
        )
