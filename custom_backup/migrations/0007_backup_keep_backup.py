# Generated by Django 5.0.6 on 2024-09-13 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_backup', '0006_backup_backup_directories'),
    ]

    operations = [
        migrations.AddField(
            model_name='backup',
            name='keep_backup',
            field=models.BooleanField(default=True),
        ),
    ]
