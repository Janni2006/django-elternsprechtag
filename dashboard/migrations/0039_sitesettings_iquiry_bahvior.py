# Generated by Django 4.2 on 2024-06-24 00:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0038_inquiry_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='iquiry_bahvior',
            field=models.JSONField(default=[{'delete': True, 'keep_for_days': 30, 'type': 0}]),
        ),
    ]
