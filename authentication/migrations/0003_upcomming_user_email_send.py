# Generated by Django 4.1 on 2023-03-13 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_alter_customuser_email_alter_customuser_first_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='upcomming_user',
            name='email_send',
            field=models.BooleanField(default=False),
        ),
    ]