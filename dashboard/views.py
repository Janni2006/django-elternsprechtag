from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from authentication.models import CustomUser, TeacherExtraData, Student, Tag
from .models import Event, TeacherStudentInquiry, SiteSettings
from django.db.models import Q
from django.utils import timezone

from django.urls import reverse

from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes

from .forms import BookForm, InquiryForm
from .decorators import lead_started, parent_required
from django.contrib import messages
from django.http import Http404

# Create your views here.


@login_required
@parent_required
def public_dashboard(request):
    students = request.user.students.all()
    inquiries = []
    for inquiry in TeacherStudentInquiry.objects.filter(Q(parent=request.user), Q(event=None)):
        inquiry_id = urlsafe_base64_encode(force_bytes(inquiry.id))
        inquiries.append({'teacher': inquiry.teacher, 'student': inquiry.student,
                         'inquiry_link': reverse('inquiry_detail_view', args=[inquiry_id])})
    booked_events = []
    for event in Event.objects.filter(Q(occupied=True), Q(parent=request.user)):
        booked_events.append({'event': event, 'url': reverse(
            'event_per_id', args=[event.id])})
    return render(request, 'dashboard/public_dashboard.html', {'inquiries': inquiries, 'booked_events': booked_events})


@login_required
@parent_required
def search(request):
    teachers = CustomUser.objects.filter(role=1)
    teacherExtraData = TeacherExtraData.objects.all()
    request_search = request.GET.get('q', None)
    if request_search is None:
        ans = 'Please enter the name of a teacher'
    elif request_search.startswith('#'):
        request_search = request_search[1:]
        result = teacher.filter(tags__icontains=request_search)
    else:
        result = teacher.filter(last_name__icontains=request_search)

    return render(request, 'dashboard/search.html', {'teachers': result, 'search': request_search})
