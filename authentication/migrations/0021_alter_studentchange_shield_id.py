# Generated by Django 4.2 on 2024-06-21 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0020_studentchange_applied_studentchange_applied_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentchange',
            name='shield_id',
            field=models.CharField(blank=True, max_length=38, null=True, unique=True),
        ),
    ]