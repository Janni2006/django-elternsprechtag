# Generated by Django 4.1 on 2022-10-02 08:30

import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0008_alter_tag_color"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tag",
            name="color",
            field=colorfield.fields.ColorField(
                default="#A2A80B", image_field=None, max_length=18, samples=None
            ),
        ),
    ]
