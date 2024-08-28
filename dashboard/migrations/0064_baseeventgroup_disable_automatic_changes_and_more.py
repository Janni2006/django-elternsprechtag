# Generated by Django 5.0.6 on 2024-08-28 01:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0063_dayeventgroup_force_dayeventgroup_manual_apply_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseeventgroup',
            name='disable_automatic_changes',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='dayeventgroup',
            name='disable_automatic_changes',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event',
            name='disable_automatic_changes',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='teachereventgroup',
            name='disable_automatic_changes',
            field=models.BooleanField(default=False),
        ),
    ]