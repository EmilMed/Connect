# Generated by Django 5.0.6 on 2024-08-12 10:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0042_alter_contact_phone_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usersettings',
            name='preferred_time_ranges',
        ),
    ]
