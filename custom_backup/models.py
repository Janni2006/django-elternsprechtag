from django.db import models
import string
import random
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.utils.translation import gettext as _
from colorfield.fields import ColorField
from django.core.exceptions import ValidationError

from PIL import Image

from .helpers import *


class BackupAppsConfigs(models.Model):
    def get_choices(*args, **kwargs):
        app_choices = []
        for app in get_all_apps():
            app_choices.append((len(app_choices), app.verbose_name))

        return app_choices

    def get_app_label(self, *args, **kwargs) -> str:
        label = list(get_all_apps())[self.referenced_app].label
        return label

    backup = models.BooleanField()
    referenced_app = models.IntegerField(choices=get_choices, unique=True)
    app_label = models.CharField(max_length=200, default="", blank=True)

    def save(self, *args, **kwargs):
        self.app_label = self.get_app_label(self)
        super(BackupAppsConfigs, self).save(*args, **kwargs)


class BackupModelConfigs(models.Model):
    def get_choices():
        model_choices = []
        for model in get_all_models():
            model_choices.append((len(model_choices), model.__name__))

        return model_choices

    def get_model_label(self, *args, **kwargs):
        model_name = get_all_models()[self.referenced_model].__qualname__
        return model_name

    backup = models.BooleanField(default=True)
    corresponding_app = models.ForeignKey(BackupAppsConfigs, on_delete=models.CASCADE)
    referenced_model = models.IntegerField(choices=get_choices, unique=True)
    model_label = models.CharField(max_length=200, default="", blank=True)

    depends_on = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )

    def check_self_dependence(
        self, object: BackupAppsConfigs, pk_list=[], *args, **kwargs
    ):
        if not object.depends_on:
            return False
        else:
            if object.pk in pk_list:
                return True
            else:
                pk_list.append(object.pk)
                return self.check_self_dependence(object.depends_on, pk_list)

    def clean(self):
        if self.depends_on:
            if self.check_self_dependence(self):
                raise ValidationError("A depenency loop was created!")

    def save(self, *args, **kwargs):
        self.model_label = self.get_model_label(self)
        super(BackupModelConfigs, self).save(*args, **kwargs)
