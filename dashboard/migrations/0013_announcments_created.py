# Generated by Django 4.1 on 2022-12-07 07:50

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0012_announcments'),
    ]

    operations = [
        migrations.AddField(
            model_name='announcments',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
