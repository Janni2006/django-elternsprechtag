# Generated by Django 4.1 on 2023-03-13 20:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0018_sitesettings_impressum'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitesettings',
            name='impressum',
            field=models.CharField(default='', max_length=200),
        ),
    ]
