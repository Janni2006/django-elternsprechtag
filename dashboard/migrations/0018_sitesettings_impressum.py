# Generated by Django 4.1 on 2023-03-13 20:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0017_alter_event_room'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='impressum',
            field=models.URLField(default=''),
        ),
    ]
