# Generated by Django 5.0.6 on 2024-10-07 07:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0075_event_base_event'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventchangeformula',
            name='type',
            field=models.IntegerField(choices=[(0, 'Submit own time periods.')], default=0),
        ),
    ]
