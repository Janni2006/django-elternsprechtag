# Generated by Django 5.1.1 on 2024-10-07 20:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0080_merge_20241007_1359'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventchangeformula',
            name='type',
            field=models.IntegerField(choices=[(0, 'Zeitfenster'), (1, 'Pausenantrag'), (2, 'Krankschreibung')], default=0),
        ),
    ]