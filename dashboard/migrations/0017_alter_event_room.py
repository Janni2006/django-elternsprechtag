# Generated by Django 4.1 on 2023-03-03 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0016_alter_announcements_announcement_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='room',
            field=models.CharField(blank=True, default=None, max_length=3, null=True),
        ),
    ]
