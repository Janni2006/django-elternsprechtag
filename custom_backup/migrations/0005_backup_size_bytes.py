# Generated by Django 5.0.6 on 2024-09-13 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_backup', '0004_alter_backup_backup_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='backup',
            name='size_bytes',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
