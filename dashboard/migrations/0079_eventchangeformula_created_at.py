# Generated by Django 5.0.6 on 2024-10-07 00:02

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0078_alter_eventchangeformula_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventchangeformula',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
    ]
