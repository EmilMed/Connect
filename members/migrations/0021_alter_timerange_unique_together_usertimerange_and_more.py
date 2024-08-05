# Generated by Django 5.0.6 on 2024-07-15 08:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0020_timerange_remove_usersettings_preferred_days_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='timerange',
            unique_together={('day', 'start_time', 'end_time')},
        ),
        migrations.CreateModel(
            name='UserTimeRange',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timerange', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='members.timerange')),
                ('usersettings', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='members.usersettings')),
            ],
        ),
    ]
