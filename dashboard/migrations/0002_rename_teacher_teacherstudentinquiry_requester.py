# Generated by Django 4.1 on 2022-09-26 20:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="teacherstudentinquiry",
            old_name="teacher",
            new_name="requester",
        ),
    ]