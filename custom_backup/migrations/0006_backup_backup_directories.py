# Generated by Django 5.0.6 on 2024-09-13 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_backup', '0005_backup_size_bytes'),
    ]

    operations = [
        migrations.AddField(
            model_name='backup',
            name='backup_directories',
            field=models.TextField(blank=True, null=True),
        ),
    ]