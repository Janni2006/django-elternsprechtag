# Generated by Django 5.0.6 on 2024-08-13 11:30

import dashboard.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0057_dayeventgroup_base_event'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseeventgroup',
            name='valid_until',
            field=models.DateField(default=dashboard.models.BaseEventGroup.get_default_valid_until),
        ),
    ]