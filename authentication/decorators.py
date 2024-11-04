import functools
from django.shortcuts import redirect, render, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

import logging

from .models import CustomUser, Upcomming_User
from .utils import (
    parent_registration_link_deprecated,
    parent_registration_check_otp_verified,
)
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

logger = logging.getLogger(__name__)


def valid_custom_user_link(view_func):
    @functools.wraps(view_func)
    def wrapper(request, user_token, key_token, *args, **kwargs):
        try:
            up_user = Upcomming_User.objects.get(
                Q(user_token=user_token), Q(access_key=key_token)
            )
        except:
            up_user = None

        if up_user and up_user.student.customuser_set.exists():
            logger.warning(
                f"There is already an existing parent ({up_user.student.customuser_set.all().first().email}) and no further parent account should be registered. Therefor the upcomming user for the student ({up_user.student.child_email}) will be deleted."
            )

            up_user.delete()

            return render(
                request, "authentication/register_parent/link_second_use_error.html"
            )

        if up_user is not None and not parent_registration_link_deprecated(up_user):
            return view_func(request, user_token, key_token, *args, **kwargs)

        return render(request, "authentication/register_parent/link_error.html")

    return wrapper


def upcomming_user_otp_validated(view_func):
    @functools.wraps(view_func)
    def wrapper(request, user_token, key_token, *args, **kwargs):
        try:
            up_user = Upcomming_User.objects.get(
                Q(user_token=user_token), Q(access_key=key_token)
            )
        except:
            up_user = None
            return render(request, "authentication/register_parent/link_error.html")

        if parent_registration_check_otp_verified(up_user):
            return view_func(request, user_token, key_token, *args, **kwargs)
        else:
            return redirect(
                "parent_check_otp",
                user_token=user_token,
                key_token=key_token,
            )

    return wrapper
