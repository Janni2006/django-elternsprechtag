from django.shortcuts import render, redirect
from django.db.models import Q
from .forms import *
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
import os
from django.views import View
from django.views.generic.base import TemplateView
from django.contrib.auth.password_validation import password_validators_help_text_html
from django.urls import reverse

from django.utils.http import urlsafe_base64_encode

from .helpers import *


def create_backup(request):
    print(get_all_models())
    print(get_all_app_models("authentication"))
    print(get_all_apps())
    return ""
