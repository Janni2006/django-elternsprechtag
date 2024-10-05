# Generated by Django 5.0.6 on 2024-09-26 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_backup', '0015_alter_backup_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='backup',
            options={'permissions': (('can_restore_backup', 'Can restore backup'), ('can_add_backup', 'Can create a backup'))},
        ),
        migrations.AlterField(
            model_name='backup',
            name='backup_file',
            field=models.FilePathField(path='/home/janni/django-elternsprechtag/backup'),
        ),
    ]
