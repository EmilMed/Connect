# Generated by Django 5.0.6 on 2024-07-18 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0026_alter_usersettings_preferred_time_ranges_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='timerange',
            name='meeting_duration',
            field=models.IntegerField(default=60),
        ),
    ]
