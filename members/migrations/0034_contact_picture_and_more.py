# Generated by Django 5.0.6 on 2024-07-23 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0033_meeting_duration_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='picture',
            field=models.ImageField(blank=True, null=True, upload_to='profile_pics/'),
        ),
        
    ]
