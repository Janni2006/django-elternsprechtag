# Generated by Django 4.2 on 2024-06-23 23:35

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0035_alter_announcements_options_alter_event_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='keep_events',
            field=models.DurationField(default=datetime.timedelta(days=30)),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='keep_student_changes',
            field=models.DurationField(default=datetime.timedelta(days=60)),
        ),
    ]