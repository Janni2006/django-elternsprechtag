# Generated by Django 5.1.1 on 2024-10-07 20:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_backup', '0021_alter_backup_validation_hash'),
    ]

    operations = [
        migrations.AlterField(
            model_name='backup',
            name='validation_hash',
            field=models.CharField(max_length=40, null=True, unique=True),
        ),
    ]
