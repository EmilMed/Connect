# Generated by Django 5.0.6 on 2024-08-12 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0043_remove_usersettings_preferred_time_ranges'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersettings',
            name='preferred_time_ranges',
            field=models.ManyToManyField(blank=True, related_name='user_settings', to='members.timerange'),
        ),
    ]
