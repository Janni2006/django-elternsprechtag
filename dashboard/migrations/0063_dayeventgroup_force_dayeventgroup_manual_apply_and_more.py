# Generated by Django 5.0.6 on 2024-08-28 00:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0062_baseeventgroup_manual_apply'),
    ]

    operations = [
        migrations.AddField(
            model_name='dayeventgroup',
            name='force',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='dayeventgroup',
            name='manual_apply',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='teachereventgroup',
            name='force',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='teachereventgroup',
            name='manual_apply',
            field=models.BooleanField(default=False),
        ),
    ]
