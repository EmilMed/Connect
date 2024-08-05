from django.core.management.base import BaseCommand
from members.models import UserSettings
from collections import defaultdict

class Command(BaseCommand):
    help = 'Remove duplicate UserSettings entries'

    def handle(self, *args, **kwargs):
        duplicates = defaultdict(list)

        # Find duplicates
        for setting in UserSettings.objects.all():
            duplicates[(setting.user_id, setting.group_id)].append(setting)

        # Remove duplicates
        for key, entries in duplicates.items():
            if len(entries) > 1:
                print(f"Found duplicates for user_id {key[0]} and group_id {key[1]}")
                for entry in entries[1:]:
                    entry.delete()

        self.stdout.write(self.style.SUCCESS('Successfully removed duplicate UserSettings entries'))