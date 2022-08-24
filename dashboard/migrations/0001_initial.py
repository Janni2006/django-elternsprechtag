# Generated by Django 4.0.4 on 2022-08-24 11:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('start', models.DateTimeField(default=django.utils.timezone.now)),
                ('end', models.DateTimeField(default=django.utils.timezone.now)),
                ('room', models.IntegerField(blank=True, default=None, null=True)),
                ('occupied', models.BooleanField(default=False)),
                ('parent', models.ForeignKey(blank=True, default=None, limit_choices_to={'role': 0}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_parent', to=settings.AUTH_USER_MODEL)),
                ('student', models.ManyToManyField(blank=True, default=None, null=True, to='authentication.student')),
                ('teacher', models.ForeignKey(limit_choices_to={'role': 1}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lead_start', models.DateField(default=django.utils.timezone.now)),
                ('lead_inquiry_start', models.DateField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TeacherStudentInquiry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField()),
                ('event', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='dashboard.event')),
                ('parent', models.ForeignKey(blank=True, default=None, limit_choices_to={'role': 0}, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_parent', to=settings.AUTH_USER_MODEL)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authentication.student')),
                ('teacher', models.ForeignKey(limit_choices_to={'role': 1}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
