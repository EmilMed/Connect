# Generated by Django 5.0.6 on 2024-07-05 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0009_alter_usersettings_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersettings',
            name='frequency',
            field=models.IntegerField(),
        ),
    ]
