# Generated by Django 4.0.4 on 2022-08-17 16:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0005_remove_sitesettings_leed_days_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sitesettings',
            old_name='leed_inquiry_start',
            new_name='lead_inquiry_start',
        ),
        migrations.RenameField(
            model_name='sitesettings',
            old_name='leed_start',
            new_name='lead_start',
        ),
    ]