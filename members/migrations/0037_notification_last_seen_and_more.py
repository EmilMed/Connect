# Generated by Django 5.0.6 on 2024-07-28 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0036_notification_event_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='last_seen',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
