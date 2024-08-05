
from django.core.management.base import BaseCommand
from members.models import Notification

class Command(BaseCommand):
    help = 'Delete notifications that have been marked as read'

    def handle(self, *args, **kwargs):
        notifications_to_delete = Notification.objects.filter(read=True)
        count_deleted, _ = notifications_to_delete.delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count_deleted} read notifications.'))
