from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import *
from django.template.loader import render_to_string
from django.contrib.auth.models import Group

from authentication.tasks import async_send_mail
from django.core.mail import send_mail
from django.conf import settings
import os

from .helpers import *


@receiver(post_save, sender=BackupAppsConfigs)
def create_model_config(sender, instance, *args, **kwargs):
    if instance.backup:
        for model in get_all_app_models(instance.app_label):
            # print(get_all_models().index(model))

            model_backup_config, created = BackupModelConfigs.objects.get_or_create(
                referenced_model=get_all_models().index(model),
                corresponding_app=instance,
            )

            model_backup_config.backup = True

            model_backup_config.save()
