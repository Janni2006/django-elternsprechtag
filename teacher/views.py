from django.shortcuts import render, redirect
from authentication.models import CustomUser
from dashboard.models import (
    Inquiry,
    Student,
    Event,
    Announcements,
    EventChangeFormula,
    LeadStatusChoices,
    TeacherEventGroup,
    DayEventGroup,
)
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.views import View
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.http import Http404
from django.utils.decorators import method_decorator
from .decorators import teacher_required, upcomming_base_event_required
from .forms import *
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from .tables import *

from general_tasks.utils import EventPDFExport

import pytz

# pdf gen
from django.http import FileResponse
import datetime

# Create your views here.

from django.urls import reverse
from django.contrib import messages
from django.utils import timezone

from dashboard.utils import check_inquiry_reopen

import logging
import operator


teacher_decorators = [login_required, teacher_required]
teacher_baseevent_decorators = [
    login_required,
    teacher_required,
    upcomming_base_event_required,
]


@login_required
@teacher_required
def dashboard(request):
    inquiries = Inquiry.objects.filter(
        Q(type=0), Q(requester=request.user), Q(processed=False)
    )
    # create individual link for each inquiry
    custom_inquiries = []
    for inquiry in inquiries:
        custom_inquiries.append(
            {
                "inquiry": inquiry,
                "url": reverse(
                    "teacher_show_inquiry",
                    args=[urlsafe_base64_encode(force_bytes(inquiry.id))],
                ),
            }
        )

    # Hier werden alle events anhand ihres Datums aufgeteilt
    events = Event.objects.filter(Q(teacher=request.user), Q(occupied=True))
    dates = []

    datetime_objects = events.order_by("start").values_list("start", flat=True)
    for datetime_object in datetime_objects:
        if timezone.localtime(datetime_object).date() not in [
            date.date() for date in dates
        ]:
            # print(datetime_object.astimezone(pytz.UTC).date())
            dates.append(datetime_object.astimezone(pytz.UTC))

    events_dict = {}
    for date in dates:
        events_dict[str(date.date())] = events.filter(
            Q(
                start__gte=timezone.datetime.combine(
                    date.date(),
                    timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
                )
            ),
            Q(
                start__lte=timezone.datetime.combine(
                    date.date(),
                    timezone.datetime.strptime("23:59:59", "%H:%M:%S").time(),
                )
            ),
        ).order_by("start")

    announcements = Announcements.objects.filter(
        Q(user=request.user), Q(read=False)
    ).order_by("-created")

    event_creation_form_open = EventChangeFormula.objects.filter(
        Q(teacher=request.user), Q(date__gte=timezone.datetime.now()), Q(status=0)
    ).exists()

    return render(
        request,
        "teacher/dashboard.html",
        {
            "inquiries": custom_inquiries,
            "events": events,
            "events_dict": events_dict,
            "announcements": announcements,
            "event_creation_form_open": event_creation_form_open,
            "cancel_event_form": cancelEventForm(),
        },
    )


@login_required
@teacher_required
def studentList(request):
    search = request.GET.get("q", None)
    page_number = request.GET.get("page")

    if search is None:
        students = Student.objects.all().order_by("first_name").order_by("last_name")
    else:
        search_split = str(search).split()
        if len(search_split) == 0:
            students = Student.objects.all()
        else:
            students = Student.objects.none()
            for key in search_split:
                queryset = Student.objects.filter(
                    Q(first_name__icontains=key) | Q(last_name__icontains=key)
                )
                if students.intersection(students, queryset).exists():
                    students = students.intersection(students, queryset)
                else:
                    students = students.union(students, queryset)

            # students = (
            #     Student.objects.filter(
            #         Q(first_name__icontains=search) | Q(last_name__icontains=search)
            #     )
            #     .order_by("first_name")
            #     .order_by("last_name")
            # )
    students = students.order_by("first_name").order_by("last_name")
    events = Event.objects.filter(Q(teacher=request.user))
    inquiries = Inquiry.objects.filter(
        Q(requester=request.user) | Q(respondent=request.user)
    ).exclude(Q(processed=True))

    students_list = []

    if students is not None:
        for student in students:
            status = 0  # No Event or Inquiry at all

            inquiry = inquiries.filter(Q(students=student)).order_by("requester__role")

            if inquiry:
                if inquiry[0].type == 0:
                    status = 1  # Teacher send inquiry
                elif inquiry[0].type == 1:
                    status = 2  # Parent send inquiry

            event = events.filter(Q(student=student))

            if event:
                if event[0].status == 1:
                    status = 3  # Event is safe

            students_list.append([student, status])

    paginator = Paginator(students_list, 25)
    page_obj = paginator.get_page(page_number)

    return render(
        request, "teacher/studentList.html", {"page_obj": page_obj, "search": search}
    )


@login_required
@teacher_required
def teacher_redirect_eventinquiry(request, studentID):
    try:
        student = Student.objects.get(id__exact=studentID)

    except Student.DoesNotExist:
        raise Http404("Student not found")

    teacher = request.user

    try:
        event = Event.objects.get(Q(teacher=teacher), Q(student=student))

    except Event.DoesNotExist:
        pass

    else:
        return redirect("teacher_event_view", event_id=event.id)

    try:
        inquiry = Inquiry.objects.get(Q(requester=teacher), Q(students=student))

    except Inquiry.DoesNotExist:
        pass

    else:
        return redirect(
            "teacher_show_inquiry", id=urlsafe_base64_encode(force_bytes(inquiry.id))
        )

    return redirect("teacher_create_inquiry_id", studentID=student.id)


@method_decorator(teacher_decorators, name="dispatch")
class InquiryView(View):
    form_class = editInquiryForm

    def get(self, request, id):
        try:
            inquiry = Inquiry.objects.get(
                Q(type=0),
                Q(id__exact=force_str(urlsafe_base64_decode(id))),
                Q(requester=request.user),
            )
        except Inquiry.DoesNotExist:
            Http404("Inquiry wurde nicht gefunden")
        else:
            initial = {
                "reason": inquiry.reason,
                "student": inquiry.students.first,
                "parent": inquiry.respondent,
                "event": inquiry.event,
            }
            form = self.form_class(initial=initial)
            return render(
                request,
                "teacher/inquiry/viewInquiry.html",
                {
                    "form": form,
                    "student": inquiry.students.first,
                    "parent_first_name": inquiry.respondent.first_name,
                    "parent_last_name": inquiry.respondent.last_name,
                    "f_inquiry_id": urlsafe_base64_encode(force_bytes(inquiry.id)),
                },
            )

    def post(self, request, id):
        try:
            inquiry = Inquiry.objects.get(
                Q(type=0), Q(id__exact=force_str(urlsafe_base64_decode(id)))
            )
        except Inquiry.DoesNotExist:
            Http404("Inquiry wurde nicht gefunden")
        else:
            initial = {
                "reason": inquiry.reason,
                "student": inquiry.students.first,
                "parent": inquiry.respondent,
                "event": inquiry.event,
            }
            form = self.form_class(request.POST, initial=initial)
            if form.is_valid():
                inquiry.reason = form.cleaned_data["reason"]
                inquiry.save()
                messages.success(request, "Änderungen angenommen")
                return redirect("teacher_dashboard")
            return render(
                request,
                "teacher/inquiry/viewInquiry.html",
                {
                    "form": form,
                    "student": inquiry.students.first,
                    "f_inquiry_id": urlsafe_base64_encode(force_bytes(inquiry.id)),
                },
            )


@method_decorator(teacher_baseevent_decorators, name="dispatch")
class DeleteInquiryView(View):
    def get(self, request, inquiryID):
        try:
            inquiry = Inquiry.objects.get(
                Q(type=0),
                Q(id__exact=force_str(urlsafe_base64_decode(inquiryID))),
                Q(requester=request.user),
            )
        except Inquiry.DoesNotExist:
            Http404("Inquiry wurde nicht gefunden")
        else:
            inquiry.delete()
            return redirect("teacher_dashboard")


@method_decorator(teacher_baseevent_decorators, name="dispatch")
class CreateInquiryView(View):
    def get(self, request, studentID):
        try:
            student = Student.objects.get(id__exact=studentID)
        except Student.DoesNotExist:
            raise Http404("Student not found")
        else:
            # redirect the user if an inquiry already exists ==> prevent the userr to create a new one
            inquiry = Inquiry.objects.filter(
                Q(type=0), Q(students=student), Q(requester=request.user)
            )
            if inquiry:
                messages.info(
                    request,
                    "Sie haben bereits eine Anfrage für dieses Kind erstellt. Im folgenden haben Sie die Möglichkeit diese Anfrage zu bearbeiten.",
                )
                return redirect(
                    "teacher_show_inquiry",
                    id=urlsafe_base64_encode(force_bytes(inquiry.first().id)),
                )

            # let the user create a new inquiry
            #! Hier muss erst überprüft werden, ob es für dieses Kind ein Elternteil gibt

            if not CustomUser.objects.filter(Q(role=0), Q(students=student)).exists():
                return render(
                    request,
                    "teacher/inquiry/noParentInquiry.html",
                    {"student": student},
                )

            parent = CustomUser.objects.filter(Q(role=0), Q(students=student)).first()

            initial = {
                "student": student,
                "parent": parent,
                "base_event": BaseEventGroup.objects.filter(
                    valid_until__gte=timezone.now()
                ).first(),
            }
            form = createInquiryForm(initial=initial)

            if (
                len(Event.objects.filter(Q(teacher=request.user), Q(student=student)))
                != 0
            ):
                messages.warning(
                    request, "Sie haben bereits einen Termin mit diesem Kind."
                )

        return render(
            request,
            "teacher/inquiry/createInquiry.html",
            {
                "form": form,
                "choices_count": form.fields["base_event"].queryset.count(),
                "student": student,
            },
        )

    def post(self, request, studentID):
        try:
            student = Student.objects.get(id__exact=studentID)
        except Student.DoesNotExist:
            raise Http404("Student not found")
        else:
            # redirect the user if an inquiry already exists ==> prevent the userr to create a new one
            inquiry = Inquiry.objects.filter(
                Q(type=0), Q(students=student), Q(requester=request.user)
            )
            if inquiry:
                messages.info(
                    request,
                    "Sie haben bereits eine Anfrage für dieses Kind erstellt. Im folgenden haben Sie die Möglichkeit diese Anfrage zu bearbeiten.",
                )
                return redirect(
                    "teacher_show_inquiry",
                    id=urlsafe_base64_encode(force_bytes(inquiry.first().id)),
                )

            #! Hier muss erst überprüft werden, ob es für dieses Kind ein Elternteil gibt
            if not CustomUser.objects.filter(Q(role=0), Q(students=student)).exists():
                return render(
                    request,
                    "teacher/inquiry/noParentInquiry.html",
                    {"student": student},
                )

            # let the user create a new inquiry
            parent = CustomUser.objects.filter(Q(role=0), Q(students=student)).first()
            initial = {"student": student, "parent": parent}
            form = createInquiryForm(request.POST, initial=initial)
            if form.is_valid():
                inquiry = Inquiry.objects.create(
                    requester=request.user,
                    respondent=form.cleaned_data["parent"],
                    reason=form.cleaned_data["reason"],
                    type=0,
                    base_event=form.cleaned_data["base_event"],
                )
                inquiry.students.set([form.cleaned_data["student"]])
                inquiry.save()
                messages.success(request, "Anfrage erstellt")
                return redirect("teacher_dashboard")
        return render(
            request,
            "teacher/inquiry/createInquiry.html",
            {
                "form": form,
                "student": student,
            },
        )


@login_required
@teacher_required
def confirm_event(request, event):
    try:
        event = Event.objects.get(Q(teacher=request.user), Q(id=event))
    except Event.DoesNotExist:
        messages.error(request, "Dieser Termin konnte nicht gefunden werden")
    else:
        if (
            event.status == 0
        ):  # * Hier wird überprüft, ob der Termin zum Zeitpunkt der Abfrage noch vergeben ist.
            messages.warning(
                request,
                "Dieser Termin ist nicht länger vergeben und kann somit nicht von Ihnen aufgerufen oder bearbeitet werden.",
            )
            return redirect("teacher_dashboard")

        event.status = 1
        event.occupied = True
        event.save()
        inquiries = event.inquiry_set.filter(
            Q(requester=event.parent), Q(processed=False)
        )
        for inquiry in inquiries:
            inquiry.processed = True
            inquiry.save()
    return redirect("teacher_dashboard")


@login_required
@teacher_required
def markAnnouncementRead(request, announcement_id):
    try:
        announcement = Announcements.objects.get(
            Q(id__exact=force_str(urlsafe_base64_decode(announcement_id)))
        )
    except Announcements.DoesNotExist:
        raise Http404("Mitteilung nicht gefunden")
    else:
        announcement.read = True
        announcement.save()
        return redirect("teacher_dashboard")


@login_required
@teacher_required
@upcomming_base_event_required
def create_event_PDF(request):
    pdf_generator = EventPDFExport(request.user.id)
    return FileResponse(
        pdf_generator.print_events(),
        as_attachment=False,
        filename=f'events_{datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")}.pdf',
        content_type="application/pdf",
    )


@method_decorator(teacher_decorators, name="dispatch")
class EventDetailView(View):
    cancel_form = cancelEventForm

    def get(self, request, event_id):
        try:
            event = Event.objects.get(Q(id=event_id), Q(teacher=request.user))
        except Event.DoesNotExist:
            raise Http404("Der Termin konnte nicht gefunden werden")
        else:
            if (
                event.status == 0
            ):  # * Hier wird überprüft, ob der Termin zum Zeitpunkt der Abfrage noch vergeben ist.
                messages.warning(
                    request,
                    "Dieser Termin ist nicht länger vergeben und kann somit nicht von Ihnen aufgerufen oder bearbeitet werden.",
                )
                return redirect("teacher_dashboard")

            inquiry_reason = None

            inquiry = Inquiry.objects.filter(
                Q(event=event), Q(requester=request.user), Q(type=0)
            )  #! so abgeändert, dass nur eine Anfrage durchgelassen wird, die auch vo Lehrer kommt

            #! Ich habe das abgeändert, damit direkt die gesamte Anfrage weitergeleitet wird.
            if inquiry:
                inquiry_reason = inquiry[0].reason

            cancel_form = self.cancel_form
            return render(
                request,
                "teacher/event/detailEvent.html",
                context={
                    "cancel_event": cancel_form,
                    "event": event,
                    # "inquiry_reason": inquiry_reason,
                    "inquiry": inquiry,
                },
            )

    def post(self, request, event_id):
        try:
            event = Event.objects.get(Q(id=event_id), Q(teacher=request.user))
        except Event.DoesNotExist:
            raise Http404("Der Termin konnte nicht gefunden werden")
        else:
            if (
                event.status == 0
            ):  # * Hier wird überprüft, ob der Termin zum Zeitpunkt der Abfrage noch vergeben ist.
                messages.warning(
                    request,
                    "Dieser Termin ist nicht länger vergeben und kann somit nicht von Ihnen aufgerufen oder bearbeitet werden.",
                )
                return redirect("teacher_dashboard")

            if "cancel_event" in request.POST:
                cancel_form = self.cancel_form(request.POST)
                if cancel_form.is_valid():
                    message = cancel_form.cleaned_data["message"]
                    book_other = cancel_form.cleaned_data["book_other_event"]

                    parent = event.parent
                    teacher = event.teacher

                    if book_other:
                        teacher_id = urlsafe_base64_encode(
                            force_bytes(event.teacher.id)
                        )
                        Announcements.objects.create(
                            announcement_type=1,
                            user=parent,
                            message="%s %s hat Ihren Termin abgesagt und folgende Nachricht für Sie hinterlassen: %s \nUnter dem angegebenen Link buchen Sie bitte einen neuen Termin"
                            % (
                                teacher.first_name,
                                teacher.last_name,
                                message,
                            ),
                            action_name="Termine ansehen",
                            action_link=reverse(
                                "event_teacher_list", args=[teacher_id]
                            ),
                        )
                    else:
                        Announcements.objects.create(
                            announcement_type=1,
                            user=parent,
                            message="%s %s hat Ihren Termin abgesagt und folgende Nachricht für Sie hinterlassen: %s"
                            % (
                                teacher.first_name,
                                teacher.last_name,
                                message,
                            ),
                        )

                    # Hier wird die vom Elternteil möglicherweise gestellte anfrage als bearbeitet angezeigt
                    try:
                        inquiry = Inquiry.objects.get(
                            Q(type=1),
                            Q(requester=parent),
                            Q(respondent=teacher),
                            Q(event=event),
                            Q(processed=False),
                        )
                    except Inquiry.DoesNotExist:
                        pass
                    except Inquiry.MultipleObjectsReturned:
                        inquiries = inquiry = Inquiry.objects.filter(
                            Q(type=1),
                            Q(requester=parent),
                            Q(respondent=teacher),
                            Q(event=event),
                            Q(processed=False),
                        )
                        for inquiry in inquiries:
                            inquiry.processed = True
                            inquiry.respondent_reaction = 2
                            inquiry.save()

                        logger = logging.getLogger(__name__)
                        logger.warn(
                            "Es waren mehrere unbeantwortete Inquiries verfügbar."
                        )
                    else:
                        inquiry.processed = True
                        inquiry.respondent_reaction = 2
                        inquiry.save()

                    check_inquiry_reopen(parent, teacher)
                    event.parent = None
                    event.status = 0
                    event.occupied = False
                    event.student.clear()
                    event.save()
                    return redirect("teacher_dashboard")

            inquiry_reason = None

            inquiry = Inquiry.objects.filter(Q(event=event), Q(requester=request.user))

            if inquiry:
                inquiry_reason = inquiry[0].reason

            cancel_form = self.cancel_form
            return render(
                request,
                "teacher/event/detailEvent.html",
                context={
                    "cancel_event": cancel_form,
                    "event": event,
                    "inquiry_reason": inquiry_reason,
                },
            )


class EventCancellationView(View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        form = cancelEventForm()

        return render(
            request,
            "teacher/teacher_form_fallback.html",
            {
                "form": form,
                "title": "Cancel event",
                "back_url": reverse("teacher_personal_events"),
            },
        )

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        form = cancelEventForm(request.POST)

        if form.is_valid():
            message = form.cleaned_data["message"]
            book_other = form.cleaned_data["book_other_event"]

            parent = event.parent
            teacher = event.teacher

            if book_other:
                teacher_id = urlsafe_base64_encode(force_bytes(event.teacher.id))
                Announcements.objects.create(
                    announcement_type=1,
                    user=parent,
                    message="%s %s hat Ihren Termin abgesagt und folgende Nachricht für Sie hinterlassen: %s \nUnter dem angegebenen Link buchen Sie bitte einen neuen Termin"
                    % (
                        teacher.first_name,
                        teacher.last_name,
                        message,
                    ),
                    action_name="Termine ansehen",
                    action_link=reverse("event_teacher_list", args=[teacher_id]),
                )
            else:
                Announcements.objects.create(
                    announcement_type=1,
                    user=parent,
                    message="%s %s hat Ihren Termin abgesagt und folgende Nachricht für Sie hinterlassen: %s"
                    % (
                        teacher.first_name,
                        teacher.last_name,
                        message,
                    ),
                )

            # Hier wird die vom Elternteil möglicherweise gestellte anfrage als bearbeitet angezeigt
            try:
                inquiry = Inquiry.objects.get(
                    Q(type=1),
                    Q(requester=parent),
                    Q(respondent=teacher),
                    Q(event=event),
                    Q(processed=False),
                )
            except Inquiry.DoesNotExist:
                pass
            except Inquiry.MultipleObjectsReturned:
                inquiries = inquiry = Inquiry.objects.filter(
                    Q(type=1),
                    Q(requester=parent),
                    Q(respondent=teacher),
                    Q(event=event),
                    Q(processed=False),
                )
                for inquiry in inquiries:
                    inquiry.processed = True
                    inquiry.respondent_reaction = 2
                    inquiry.save()

                logger = logging.getLogger(__name__)
                logger.warn("Es waren mehrere unbeantwortete Inquiries verfügbar.")
            else:
                inquiry.processed = True
                inquiry.respondent_reaction = 2
                inquiry.save()

            check_inquiry_reopen(parent, teacher)
            event.parent = None
            event.status = 0
            event.occupied = False
            event.student.clear()
            event.save()

            messages.success(request, "The event was successfully canceled.")

            return redirect("teacher_personal_events")

        return render(
            request,
            "teacher/teacher_form_fallback.html",
            {
                "form": form,
                "title": "Cancel event",
                "back_url": reverse("teacher_personal_events"),
            },
        )


@login_required
@teacher_required
def viewMyEvents(request):
    event_change_formulas = EventChangeFormula.objects.filter(
        Q(teacher=request.user),
        Q(date__gte=timezone.datetime.now()),
        Q(status=0) | Q(status=1),
    )

    custom_event_change_formulas = []
    for form in event_change_formulas:
        custom_event_change_formulas.append(
            {
                "change_form": form,
                "no_events_form": EventChangeFormulaPeriodForm(
                    instance=form, initial={"no_events": True}
                ),
                "link": reverse(
                    "teacher_personal_events_edit",
                    args=[urlsafe_base64_encode(force_bytes(form.id))],
                ),
            }
        )

    closed_formulars = EventChangeFormula.objects.filter(
        Q(teacher=request.user),
        Q(date__gte=timezone.datetime.now()),
        Q(status=2) | Q(status=3) | Q(status=4),
    ).order_by("created_at")

    teacher = request.user

    events = Event.objects.filter(Q(teacher=teacher))

    events_dt = Event.objects.filter(Q(teacher=teacher))

    dates = []
    datetime_objects = events_dt.order_by("start").values_list("start", flat=True)
    for datetime_object in datetime_objects:
        if timezone.localtime(datetime_object).date() not in [
            date.date() for date in dates
        ]:
            dates.append(datetime_object.astimezone(pytz.UTC))

    events_dt_dict = {}
    events_table_dict = {}
    for date in dates:
        events_dt_dict[str(date.date())] = {
            "events": Event.objects.filter(
                Q(teacher=teacher),
                Q(
                    start__gte=timezone.datetime.combine(
                        date.date(),
                        timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
                    )
                ),
                Q(
                    start__lte=timezone.datetime.combine(
                        date.date(),
                        timezone.datetime.strptime("23:59:59", "%H:%M:%S").time(),
                    )
                ),
            ).order_by("start"),
            "table": PersonalEventsTable(
                data=Event.objects.filter(
                    Q(teacher=teacher),
                    Q(
                        start__gte=timezone.datetime.combine(
                            date.date(),
                            timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
                        )
                    ),
                    Q(
                        start__lte=timezone.datetime.combine(
                            date.date(),
                            timezone.datetime.strptime("23:59:59", "%H:%M:%S").time(),
                        )
                    ),
                ),
                order_by="start",
            ),
            "sick_leave": EventChangeFormula.objects.filter(
                Q(type=EventChangeFormula.FormularTypeChoices.ILLNESS),
                Q(day_group__in=DayEventGroup.objects.filter(date=date.date())),
                Q(teacher=teacher),
            ),
            # "free_events": Event.objects.filter(
            #     Q(teacher=teacher),
            #     Q(
            #         start__gte=timezone.datetime.combine(
            #             date.date(),
            #             timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
            #         )
            #     ),
            #     Q(
            #         start__lte=timezone.datetime.combine(
            #             date.date(),
            #             timezone.datetime.strptime("23:59:59", "%H:%M:%S").time(),
            #         )
            #     ),
            #     ~Q(status=Event.StatusChoices.OCCUPIED),
            # ).count(),
            # "occupied_events": Event.objects.filter(
            #     Q(teacher=teacher),
            #     Q(
            #         start__gte=timezone.datetime.combine(
            #             date.date(),
            #             timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
            #         )
            #     ),
            #     Q(
            #         start__lte=timezone.datetime.combine(
            #             date.date(),
            #             timezone.datetime.strptime("23:59:59", "%H:%M:%S").time(),
            #         )
            #     ),
            #     Q(status=Event.StatusChoices.OCCUPIED),
            #     ~Q(lead_status=LeadStatusChoices.NOBODY),
            # ).count(),
            # "occupied_percent": int(
            #     (
            #         Event.objects.filter(
            #             Q(teacher=teacher),
            #             Q(
            #                 start__gte=timezone.datetime.combine(
            #                     date.date(),
            #                     timezone.datetime.strptime(
            #                         "00:00:00", "%H:%M:%S"
            #                     ).time(),
            #                 )
            #             ),
            #             Q(
            #                 start__lte=timezone.datetime.combine(
            #                     date.date(),
            #                     timezone.datetime.strptime(
            #                         "23:59:59", "%H:%M:%S"
            #                     ).time(),
            #                 )
            #             ),
            #             Q(status=Event.StatusChoices.OCCUPIED),
            #             ~Q(lead_status=LeadStatusChoices.NOBODY),
            #         ).count()
            #         / Event.objects.filter(
            #             Q(teacher=teacher),
            #             Q(
            #                 start__gte=timezone.datetime.combine(
            #                     date.date(),
            #                     timezone.datetime.strptime(
            #                         "00:00:00", "%H:%M:%S"
            #                     ).time(),
            #                 )
            #             ),
            #             Q(
            #                 start__lte=timezone.datetime.combine(
            #                     date.date(),
            #                     timezone.datetime.strptime(
            #                         "23:59:59", "%H:%M:%S"
            #                     ).time(),
            #                 )
            #             ),
            #             ~Q(lead_status=LeadStatusChoices.NOBODY),
            #         ).count()
            #     )
            #     * 100
            # ),
        }
        events_table_dict[str(date.date())] = PersonalEventsTable(
            data=Event.objects.filter(
                Q(teacher=teacher),
                Q(
                    start__gte=timezone.datetime.combine(
                        date.date(),
                        timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
                    )
                ),
                Q(
                    start__lte=timezone.datetime.combine(
                        date.date(),
                        timezone.datetime.strptime("23:59:59", "%H:%M:%S").time(),
                    )
                ),
            ),
            order_by="start",
        )

    if Event.objects.filter(
        Q(teacher=teacher),
        Q(start__gte=timezone.now()),
        ~Q(lead_status=LeadStatusChoices.NOBODY),
    ).exists():
        occupied_percent = int(
            (
                Event.objects.filter(
                    Q(teacher=teacher),
                    Q(start__gte=timezone.now()),
                    Q(status=Event.StatusChoices.OCCUPIED),
                    ~Q(lead_status=LeadStatusChoices.NOBODY),
                ).count()
                / Event.objects.filter(
                    Q(teacher=teacher),
                    Q(start__gte=timezone.now()),
                    ~Q(lead_status=LeadStatusChoices.NOBODY),
                ).count()
            )
            * 100
        )
    else:
        occupied_percent = 0

    return render(
        request,
        "teacher/event/myEvents.html",
        {
            "open_formulas": custom_event_change_formulas,
            "closed_formulas": closed_formulars,
            "events": events,
            "events_dt": events_dt,
            "events_dt_dict": events_dt_dict,
            "events_table_dict": events_table_dict,
            "break_form": BreakFormularCreationForm(),
            "sick_leave_form": SickLeaveForm(teacher=request.user),
            "statistics": {
                "total": Event.objects.filter(
                    Q(teacher=teacher), Q(start__gte=timezone.now())
                ),
                "free_events": Event.objects.filter(
                    Q(teacher=teacher),
                    Q(start__gte=timezone.now()),
                    ~Q(status=Event.StatusChoices.OCCUPIED),
                ).count(),
                "occupied_events": Event.objects.filter(
                    Q(teacher=teacher),
                    Q(start__gte=timezone.now()),
                    Q(status=Event.StatusChoices.OCCUPIED),
                    ~Q(lead_status=LeadStatusChoices.NOBODY),
                ).count(),
                "occupied_percent": occupied_percent,
            },
            "page_under_construction": True,
        },
    )


@method_decorator(teacher_decorators, name="dispatch")
class EditMyEventsDetail(View):
    def get(self, request, form_id):
        event_change_formula = get_object_or_404(
            EventChangeFormula, id=force_str(urlsafe_base64_decode(form_id))
        )

        match event_change_formula.type:
            case EventChangeFormula.FormularTypeChoices.TIME_PERIODS:
                form = EventChangeFormulaPeriodForm(instance=event_change_formula)
            case EventChangeFormula.FormularTypeChoices.ILLNESS:
                form = EventChangeFormulaPeriodForm(instance=event_change_formula)
            case EventChangeFormula.FormularTypeChoices.BREAKS:
                form = EventChangeFormulaBreakForm(instance=event_change_formula)
            case _:
                print("Wrong type")
        print(form)

        return render(
            request,
            "teacher/event/myEventsEditFormula.html",
            {"formula": event_change_formula, "form": form},
        )

    def post(self, request, form_id):
        try:
            event_change_formula = EventChangeFormula.objects.get(
                id=force_str(urlsafe_base64_decode(form_id))
            )
        except EventChangeFormula.DoesNotExist:
            raise Http404("The formula ould not be found.")

        match event_change_formula.type:
            case EventChangeFormula.FormularTypeChoices.TIME_PERIODS:
                form = EventChangeFormulaPeriodForm(
                    request.POST, instance=event_change_formula
                )
            case EventChangeFormula.FormularTypeChoices.ILLNESS:
                form = EventChangeFormulaPeriodForm(
                    request.POST, instance=event_change_formula
                )
            case EventChangeFormula.FormularTypeChoices.BREAKS:
                form = EventChangeFormulaBreakForm(
                    request.POST, instance=event_change_formula
                )
        # form = EventChangeFormulaPeriodForm(request.POST, instance=event_change_formula)

        if form.is_valid():
            form.save()
            if form.cleaned_data.get("no_events", False):
                messages.success(
                    request,
                    "Sie haben erfolgreich angefragt, dass Sie am {} keine Termine haben.".format(
                        event_change_formula.date
                    ),
                )
            return redirect("teacher_personal_events")

        return render(
            request,
            "teacher/event/myEventsEditFormula.html",
            {"formula": event_change_formula, "form": form},
        )


# @method_decorator(teacher_decorators, name="dispatch")
# class EventListView(View):  # ???????? was war das nochmal?
#     def get(self, request):
#         events = Event.objects.filter(Q(teacher=request.user), Q(occupied=True))
#         dates = []

#         datetime_objects = events.order_by("start").values_list("start", flat=True)
#         for datetime_object in datetime_objects:
#             if timezone.localtime(datetime_object).date() not in [
#                 date.date() for date in dates
#             ]:
#                 # print(datetime_object.astimezone(pytz.UTC).date())
#                 dates.append(datetime_object.astimezone(pytz.UTC))

#         events_dict = {}
#         for date in dates:
#             #! Spontane Änderung aufgrund von Problemen auf dem Server
#             events_dict[str(date.date())] = events.filter(
#                 Q(
#                     start__gte=timezone.datetime.combine(
#                         date.date(),
#                         timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
#                     )
#                 ),
#                 Q(
#                     start__lte=timezone.datetime.combine(
#                         date.date(),
#                         timezone.datetime.strptime("23:59:59", "%H:%M:%S").time(),
#                     )
#                 ),
#             ).order_by("start")


class EventBreakRequestView(View):
    def get(self, request):
        form = BreakFormularCreationForm()

        return (
            render(
                request,
                "teacher/teacher_form_fallback.html",
                {
                    "form": form,
                    "page_under_construction": True,
                    "title": _("Break period request"),
                    "back_url": reverse("teacher_personal_events"),
                },
            ),
        )

    def post(self, request):

        form = BreakFormularCreationForm(data=request.POST)

        if form.is_valid():
            day_group = form.cleaned_data["day_group"]
            start_time = form.cleaned_data["start_time"]
            end_time = form.cleaned_data["end_time"]
            try:
                teacher_group = TeacherEventGroup.objects.get(
                    Q(teacher=request.user), Q(day_group=day_group)
                )
            except TeacherEventGroup.MultipleObjectsReturned:
                raise ValueError("Only one teachergroup should exist per date.")

            start_datetime = timezone.datetime.combine(
                date=day_group.date, time=start_time
            )
            end_datetime = timezone.datetime.combine(date=day_group.date, time=end_time)

            events = Event.objects.filter(
                Q(teacher_event_group=teacher_group),
                Q(start__gte=start_datetime),
                Q(end__lte=end_datetime),
            )

            if not Event.StatusChoices.UNOCCUPIED in events.values_list(
                "status", flat=True
            ):
                messages.error(
                    request,
                    _(
                        "All events are already occupied. If you want to set your break to this period anyways please get in touch with the system operators."
                    ),
                )
                return redirect("teacher_personal_events")

            if not events.exclude(
                Q(lead_status=LeadStatusChoices.NOBODY), Q(lead_manual_override=True)
            ).exists():
                messages.warning(
                    request,
                    "There are no events changes can be applied to. Abbort formular creation.",
                )
                return redirect("teacher_personal_events")

            if Event.StatusChoices.INQUIRY in events.values_list(
                "status", flat=True
            ) or Event.StatusChoices.OCCUPIED in events.values_list(
                "status", flat=True
            ):
                messages.info(
                    request,
                    _(
                        "The break request can not be applied to all events within the requested time period because some of the events are occupied."
                    ),
                )

            formular = EventChangeFormula.objects.create(
                type=EventChangeFormula.FormularTypeChoices.BREAKS,
                day_group=teacher_group.day_group,
                teacher_event_group=teacher_group,
                teacher=request.user,
                date=teacher_group.day_group.date,
                start_time=start_time,
                end_time=end_time,
                status=EventChangeFormula.FormularStatusChoices.PENDING_CONFIRMATION,
            )
            formular.save()

            messages.success(
                request,
                "The break request was successfully created. Please wait until an authorized person approves your request.",
            )

            return redirect("teacher_personal_events")
        return render(
            request,
            "teacher/teacher_form_fallback.html",
            {"form": form, "page_under_construction": True},
        )


class EventBreakForEventRequestView(View):
    def get(self, request, event_pk):
        event = get_object_or_404(Event, teacher=request.user, pk=event_pk)

        if not event.status == Event.StatusChoices.UNOCCUPIED:
            messages.error(
                request,
                "This event is already occupied. If you want to set your break to this event anyways please get in touch with the system operators.",
            )
        elif (
            event.lead_status == LeadStatusChoices.NOBODY
            and event.lead_manual_override == True
        ):
            messages.info(
                request,
                "It is already impossible for anyone to book this event at any time. No further action is required.",
            )
        else:
            print()
            formular = EventChangeFormula.objects.create(
                type=EventChangeFormula.FormularTypeChoices.BREAKS,
                day_group=event.day_group,
                teacher_event_group=event.teacher_event_group,
                teacher=request.user,
                date=event.day_group.date,
                start_time=event.start.astimezone(),
                end_time=event.end.astimezone(),
                status=EventChangeFormula.FormularStatusChoices.PENDING_CONFIRMATION,
            )
            formular.save()

            messages.success(
                request,
                "The break request was successfully created. Please wait until an authorized person approves your request.",
            )

        return redirect("teacher_personal_events")


class EventResetLeadStatusToOriginalView(View):
    def get(self, request, event_pk):
        event = get_object_or_404(Event, pk=event_pk, teacher=request.user)
        teacher_group = event.teacher_event_group

        if event.lead_status >= teacher_group.lead_status:
            messages.error(
                request, "You are not allowed to change the lead status of this object."
            )

            return redirect("teacher_personal_events")

        event.lead_manual_override = teacher_group.lead_manual_override
        event.disable_automatic_changes = teacher_group.disable_automatic_changes
        event.lead_status = teacher_group.lead_status
        event.save()

        messages.success(
            request, "The lead status was successfully reset to its original state."
        )

        return redirect("teacher_personal_events")


class EventSickLeaveRequestView(View):
    def get(self, request):
        form = SickLeaveForm(teacher=request.user)

        return render(
            request,
            "teacher/teacher_form_fallback.html",
            {
                "form": form,
                "page_under_construction": True,
                "title": _("Sick leave request"),
                "back_url": reverse("teacher_personal_events"),
            },
        )

    def post(self, request):
        form = SickLeaveForm(data=request.POST, teacher=request.user)
        if form.is_valid():
            form.save()
            return redirect("teacher_personal_events")
        return render(
            request,
            "teacher/teacher_form_fallback.html",
            {
                "form": form,
                "page_under_construction": True,
                "title": _("Sick leave request"),
                "back_url": reverse("teacher_personal_events"),
            },
        )


class DeleteEventFormularView(View):
    def get(self, request, pk):
        formular = get_object_or_404(EventChangeFormula, pk=pk)

        if formular.type == EventChangeFormula.FormularTypeChoices.TIME_PERIODS:
            messages.error(request, "You can´t remove this formular.")

            return redirect("teacher_personal_events")

        print(formular)

        formular.status = EventChangeFormula.FormularStatusChoices.REMOVED
        formular.save()

        messages.success(request, "Formular was successfully removed.")
        return redirect("teacher_personal_events")
