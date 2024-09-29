# Generated by Django 5.0.6 on 2024-09-26 16:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0070_alter_event_options_alter_baseeventgroup_lead_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dayeventgroup',
            name='lead_status',
            field=models.IntegerField(choices=[(0, 'Niemand kann diesen Termin aktuell anfragen.'), (1, 'Nur Eltern mit besonderen Berechtigungen können diesen Termin aktuell anfragen.'), (2, 'Nur Eltern, die eine Anfrage der Lehrkraft bekommen haben, können diesen Termin aktuell anfragen.'), (3, 'Alle Eltern können diesen Termin aktuell anfragen.')], default=1),
        ),
        migrations.AlterField(
            model_name='teachereventgroup',
            name='lead_status',
            field=models.IntegerField(choices=[(0, 'Niemand kann diesen Termin aktuell anfragen.'), (1, 'Nur Eltern mit besonderen Berechtigungen können diesen Termin aktuell anfragen.'), (2, 'Nur Eltern, die eine Anfrage der Lehrkraft bekommen haben, können diesen Termin aktuell anfragen.'), (3, 'Alle Eltern können diesen Termin aktuell anfragen.')], default=1),
        ),
    ]