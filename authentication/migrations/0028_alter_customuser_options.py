# Generated by Django 5.0.6 on 2024-09-24 09:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "authentication",
            "0027_alter_customuser_options_alter_student_options_and_more",
        ),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="customuser",
            options={"verbose_name": "User", "verbose_name_plural": "Benutzer"},
        ),
    ]
