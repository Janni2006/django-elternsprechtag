# Generated by Django 4.1 on 2023-03-13 20:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0019_alter_sitesettings_impressum'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitesettings',
            name='impressum',
            field=models.URLField(default=''),
        ),
    ]
