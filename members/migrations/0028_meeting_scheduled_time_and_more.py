# Generated by Django 5.0.6 on 2024-07-21 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0027_timerange_meeting_duration_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='scheduled_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
