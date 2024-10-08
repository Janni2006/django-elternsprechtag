# Generated by Django 5.0.6 on 2024-09-10 11:46

import authentication.models
import colorfield.fields
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0025_alter_tag_color'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customuser',
            options={'verbose_name': 'Benutzer', 'verbose_name_plural': 'Users'},
        ),
        migrations.AlterModelOptions(
            name='student',
            options={'verbose_name': 'Student', 'verbose_name_plural': 'Students'},
        ),
        migrations.AlterModelOptions(
            name='teacherextradata',
            options={'verbose_name': 'Additional data for teacher', 'verbose_name_plural': 'Additional data for teachers'},
        ),
        migrations.AlterModelOptions(
            name='upcomming_user',
            options={'verbose_name': 'Future user', 'verbose_name_plural': 'Future users'},
        ),
        migrations.AlterField(
            model_name='customuser',
            name='date_joined',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date joined'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(max_length=254, unique=True, verbose_name='E-Mail-Adresse'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='first_name',
            field=models.CharField(blank=True, default='', max_length=48, verbose_name='First name'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='last_name',
            field=models.CharField(blank=True, default='', max_length=48, verbose_name='Last name'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.IntegerField(choices=[(0, 'Parent'), (1, 'Teacher'), (2, 'Others')], default=2, verbose_name='Role'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='students',
            field=models.ManyToManyField(blank=True, to='authentication.student', verbose_name='Students'),
        ),
        migrations.AlterField(
            model_name='student',
            name='child_email',
            field=models.EmailField(max_length=200, null=True, verbose_name='Child emails'),
        ),
        migrations.AlterField(
            model_name='student',
            name='class_name',
            field=models.CharField(default='', max_length=4, verbose_name='Name of class'),
        ),
        migrations.AlterField(
            model_name='student',
            name='first_name',
            field=models.CharField(max_length=48, verbose_name='First name'),
        ),
        migrations.AlterField(
            model_name='student',
            name='last_name',
            field=models.CharField(max_length=48, verbose_name='Last name'),
        ),
        migrations.AlterField(
            model_name='student',
            name='registered',
            field=models.BooleanField(default=False, verbose_name='Childs parents have registered'),
        ),
        migrations.AlterField(
            model_name='studentchange',
            name='child_email',
            field=models.EmailField(blank=True, max_length=200, null=True, verbose_name='Child emails'),
        ),
        migrations.AlterField(
            model_name='studentchange',
            name='class_name',
            field=models.CharField(blank=True, max_length=4, null=True, verbose_name='Name of class'),
        ),
        migrations.AlterField(
            model_name='studentchange',
            name='first_name',
            field=models.CharField(blank=True, max_length=48, null=True, verbose_name='First name'),
        ),
        migrations.AlterField(
            model_name='studentchange',
            name='last_name',
            field=models.CharField(blank=True, max_length=48, null=True, verbose_name='Last name'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='color',
            field=colorfield.fields.ColorField(default=authentication.models.generate_new_color, image_field=None, max_length=25, samples=None, verbose_name='Colour'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=32, verbose_name='General name'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='synonyms',
            field=models.TextField(blank=True, null=True, verbose_name='Synonyms'),
        ),
        migrations.AlterField(
            model_name='teacherextradata',
            name='acronym',
            field=models.CharField(default='', max_length=3, verbose_name='Acronym'),
        ),
        migrations.AlterField(
            model_name='teacherextradata',
            name='image',
            field=models.ImageField(default='default.jpg', upload_to='teacher_pics/', verbose_name='Profile image'),
        ),
        migrations.AlterField(
            model_name='teacherextradata',
            name='room',
            field=models.IntegerField(blank=True, null=True, verbose_name='Room'),
        ),
        migrations.AlterField(
            model_name='teacherextradata',
            name='teacher',
            field=models.OneToOneField(limit_choices_to={'role': 1}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User object of the teacher'),
        ),
        migrations.AlterField(
            model_name='upcomming_user',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Time of creation'),
        ),
        migrations.AlterField(
            model_name='upcomming_user',
            name='otp',
            field=models.CharField(default=authentication.models.generate_unique_otp, max_length=6, verbose_name='OTP key'),
        ),
        migrations.AlterField(
            model_name='upcomming_user',
            name='otp_verified',
            field=models.BooleanField(default=False, verbose_name='OTP key was verified'),
        ),
        migrations.AlterField(
            model_name='upcomming_user',
            name='user_token',
            field=models.CharField(default=authentication.models.generate_unique_code, max_length=12, primary_key=True, serialize=False, verbose_name='User token'),
        ),
    ]
