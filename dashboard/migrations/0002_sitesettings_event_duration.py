# Generated by Django 4.1 on 2022-08-26 21:45

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="event_duration",
            field=models.DurationField(default=datetime.timedelta(0)),
        ),
    ]