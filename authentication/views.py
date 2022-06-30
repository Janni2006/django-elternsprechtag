from django.shortcuts import render, redirect
from .models import Upcomming_User
from django.db.models import Q
from .forms import *
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext as _

# Create your views here.


def register(request, user_token, key_token):
    if user_token is None or key_token is None:
        return redirect("help_register")

    user_data = Upcomming_User.objects.filter(
        Q(user_token=user_token), Q(access_key=key_token))

    if not user_data.exists():
        return render(request, 'authentication/register/link_error.html')

    user_data = user_data.first()

    if user_data.otp_verified:
        # check if otp was set to verified in last 3 hours
        if user_data.otp_verified_date + timezone.timedelta(hours=3) > timezone.now():
            if request.GET.get('login', False) and request.user.is_authenticated:
                user = request.user
                user.students.add(user_data.student)
                user_data.delete()

                return redirect("home")

            if request.GET.get('register', False):
                print("register")

            # view to choose between registering a new user and logging in
            return render(request, "authentication/register/register_choose.html", {'child_name': user_data.student, 'path': request.get_full_path()})
        else:  # otp was verified more than 3 hours ago
            messages.warning(
                request, _("The validation has timed out, please reenter your pin"))
            user_data.otp_verified = False
            user_data.save()

    if request.method == 'POST':
        form = Register_OTP(request.POST)

        if form.is_valid():
            if user_data.otp != form.cleaned_data['otp']:
                # report the error to the user
                messages.error(request, _("The code is invalid"))
            else:
                user_data.otp_verified = True
                user_data.otp_verified_date = timezone.now()
                user_data.save()
                return render(request, "authentication/register/register_choose.html", {'child_name': user_data.student, 'path': request.get_full_path()})

    else:
        form = Register_OTP()

    return render(request, 'authentication/register/register_otp.html', {'otp_form': form})
