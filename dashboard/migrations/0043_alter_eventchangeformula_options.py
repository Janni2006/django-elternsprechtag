# Generated by Django 4.2 on 2024-07-06 00:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0042_sitesettings_delete_event_change_formulas_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='eventchangeformula',
            options={'permissions': [('approve_disapprove', 'Can approve/disapprove the formulars for other users')], 'verbose_name': 'Termin-Änderungsantrag', 'verbose_name_plural': 'Termin-Änderungsanträge'},
        ),
    ]