# Generated by Django 4.1 on 2022-09-27 21:20

import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0002_tags"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tags",
            name="color",
            field=colorfield.fields.ColorField(
                default="#43EE07", image_field=None, max_length=18, samples=None
            ),
        ),
    ]
