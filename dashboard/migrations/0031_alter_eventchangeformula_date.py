# Generated by Django 4.2 on 2023-10-24 14:37

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0030_alter_eventchangeformula_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventchangeformula',
            name='date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Datum'),
        ),
    ]