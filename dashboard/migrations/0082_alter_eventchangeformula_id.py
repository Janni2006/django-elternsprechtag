# Generated by Django 5.1.1 on 2024-10-11 09:39

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0081_alter_eventchangeformula_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventchangeformula',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, unique=True),
        ),
    ]