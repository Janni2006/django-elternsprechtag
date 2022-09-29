# Generated by Django 4.1 on 2022-09-19 07:59

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authentication', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.IntegerField(choices=[(0, 'Elternsprechtag'), (1, 'Sprechstunde'), (2, 'Others')], default=2, verbose_name='Type')),
                ('room', models.CharField(blank=True, default=None, max_length=48)),
                ('extra_config', models.JSONField(null=True)),
                ('teachers', models.ManyToManyField(blank=True, default=None, limit_choices_to={'role': 1}, null=True, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('start', models.DateTimeField(default=django.utils.timezone.now)),
                ('end', models.DateTimeField(default=django.utils.timezone.now)),
                ('occupied', models.BooleanField(default=False)),
                ('base_event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.baseevent')),
                ('parent', models.ForeignKey(blank=True, default=None, limit_choices_to={'role': 0}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_parent', to=settings.AUTH_USER_MODEL)),
                ('student', models.ManyToManyField(blank=True, default=None, to='authentication.student')),
                ('teacher', models.ForeignKey(limit_choices_to={'role': 1}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lead_start', models.DateField(default=django.utils.timezone.now)),
                ('lead_inquiry_start', models.DateField(default=django.utils.timezone.now)),
                ('event_duration', models.DurationField(default=datetime.timedelta(0))),
                ('time_start', models.TimeField(default=django.utils.timezone.now)),
                ('time_end', models.TimeField(default=django.utils.timezone.now)),
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
