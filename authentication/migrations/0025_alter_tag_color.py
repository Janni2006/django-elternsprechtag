# Generated by Django 5.0.6 on 2024-09-11 02:42

import authentication.models
import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0024_alter_studentchange_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='color',
            field=colorfield.fields.ColorField(default=authentication.models.generate_new_color, image_field=None, max_length=25, samples=None, verbose_name='Farbe'),
        ),
    ]
