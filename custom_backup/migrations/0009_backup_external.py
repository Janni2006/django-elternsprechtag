# Generated by Django 5.0.6 on 2024-09-13 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_backup', '0008_backup_validation_hash'),
    ]

    operations = [
        migrations.AddField(
            model_name='backup',
            name='external',
            field=models.BooleanField(default=False),
        ),
    ]