from django.urls import path
from django.views.generic.base import RedirectView

urlpatterns = [
    path('redirect/wiki', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_mainpage'),
    path('redirect/wiki/public_dashboard', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/books/startseite'), name='wiki_public_dashboard'),
    path('redirect/wiki/parent_search', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_parent_search'),
    path('redirect/wiki/parent_got_inquiry', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_parent_got_inquiry'),
    path('redirect/wiki/parent_answered_inquiry', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_parent_answered_inquiry'),
    path('redirect/wiki/parent_book', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_book'),
    path('redirect/wiki/parent_event_occupied', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_error_event_occupied'),
    path('redirect/wiki/parent_view_teacher', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_parent_view_teacher'),
    path('redirect/wiki/parent_view_event', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_parent_view_event'),
    path('redirect/wiki/error_inquiry_occupied', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_error_inquiry_occupied'),
    path('redirect/wiki/error_lead_not_started', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_error_lead_not_started'),
    path('redirect/wiki/announcements', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_announcements'),
    path('redirect/wiki/my_profile', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_my_profile'),
    path('redirect/wiki/change_password', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_change_password'),
    path('redirect/wiki/student_list', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_student_list'),
    path('redirect/wiki/change_tags', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_change_tags'),
]