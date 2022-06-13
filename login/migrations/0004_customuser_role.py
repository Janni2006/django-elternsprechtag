# Generated by Django 4.0.4 on 2022-06-13 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0003_customuser_first_name_customuser_is_parent_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='role',
            field=models.IntegerField(choices=[(0, 'Parent'), (1, 'Teacher'), (2, 'Others')], default=2),
        ),
    ]
