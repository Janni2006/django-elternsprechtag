# Generated by Django 4.2 on 2023-10-14 20:58

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0023_alter_eventchangeformula_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventchangeformula',
            name='date',
            field=models.DateField(default=datetime.datetime(2023, 10, 14, 20, 58, 36, 216720, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='eventchangeformula',
            name='end_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='eventchangeformula',
            name='start_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
