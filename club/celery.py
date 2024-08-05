from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'club.settings')

app = Celery('club')

import django
django.setup()

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_schedule = {
    'generate-notifications-every-minute': {
        'task': 'members.tasks.generate_notifications',
        'schedule': crontab(minute='*/1'),
    },
     'delete-read-notifications-every-minute': {
        'task': 'members.tasks.delete_read_notifications',
        'schedule': crontab(minute='*/2'),
    },
    'generate-birthday-notifications-every-day': {
        'task': 'members.tasks.generate_birthday_notifications',
        'schedule': crontab(minute=0, hour=0),
    },
}