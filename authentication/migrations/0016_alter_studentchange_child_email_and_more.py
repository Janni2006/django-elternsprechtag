# Generated by Django 4.2 on 2024-06-21 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0015_studentchange_shield_id_alter_studentchange_student'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentchange',
            name='child_email',
            field=models.EmailField(blank=True, max_length=200, null=True, verbose_name='Email des Kindes'),
        ),
        migrations.AlterField(
            model_name='studentchange',
            name='class_name',
            field=models.CharField(blank=True, max_length=4, null=True, verbose_name='Klassenname'),
        ),
        migrations.AlterField(
            model_name='studentchange',
            name='first_name',
            field=models.CharField(blank=True, max_length=48, null=True, verbose_name='Vorname'),
        ),
        migrations.AlterField(
            model_name='studentchange',
            name='last_name',
            field=models.CharField(blank=True, max_length=48, null=True, verbose_name='Nachname'),
        ),
        migrations.AlterField(
            model_name='studentchange',
            name='shield_id',
            field=models.CharField(max_length=38, unique=True),
        ),
    ]