# Generated by Django 5.0.6 on 2024-09-25 23:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0028_alter_customuser_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='studentchange',
            options={'permissions': [('apply_changes', 'Kann Änderungen an Schüler*innen vornehmen')]},
        ),
        migrations.AlterField(
            model_name='teacherextradata',
            name='acronym',
            field=models.CharField(default='', max_length=3, verbose_name='Kürzel'),
        ),
    ]