from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [path("create/", create_backup)]
