import random
from datetime import timedelta, datetime, time
from django.utils import timezone
from members.models import Notification, UserSettings, Meeting, Group, Contact
from celery import shared_task
from club.celery import app
from .constants import DAYS_OF_WEEK

@shared_task
def delete_read_notifications():
    time_threshold = timezone.now() - timedelta(minutes=1)
    Notification.objects.filter(read=True, timestamp__lt=time_threshold).delete()

import logging

logger = logging.getLogger(__name__)

@shared_task
def generate_notifications():
    logger.info("Starting to generate notifications...")
    now = timezone.now()
    if timezone.is_naive(now):
        now = timezone.make_aware(now, timezone.get_current_timezone())
    
    for group in Group.objects.all():
        for contact in group.contacts.all():
            user = group.user
            last_meeting = Meeting.objects.filter(user=user, group=group, person_met=contact).order_by('-timestamp').first()
            user_settings = UserSettings.objects.filter(user=user, group=group).first()
            future_meeting_exists = Meeting.objects.filter(user=user, group=group, person_met=contact, scheduled_time__gte=now).exists()
            
            if future_meeting_exists:
                logger.info(f"Future meeting already scheduled for {user.username} and {contact.name} from {group.name}. Skipping notification.")
                continue
            
            if user_settings:
                frequency = user_settings.frequency
                time_ranges = user_settings.preferred_time_ranges.all()

                preferred_days = [tr.day for tr in time_ranges]
                preferred_start_times = {tr.day: tr.start_time for tr in time_ranges}
                preferred_end_times = {tr.day: tr.end_time for tr in time_ranges}

                if last_meeting:
                    last_meeting_time = last_meeting.timestamp
                    if timezone.is_naive(last_meeting_time):
                        last_meeting_time = timezone.make_aware(last_meeting_time, timezone.get_current_timezone())
                    
                    time_since_last_meeting = now - last_meeting_time
                    if time_since_last_meeting > timedelta(minutes=frequency):
                        message = f"Remember to check in with {contact.name} from {group.name}!"
                        suggested_time = schedule_meeting_time(
                            now, preferred_start_times, preferred_end_times, preferred_days
                        )
                        if suggested_time:
                            Notification.objects.create(
                                user=user,
                                message=message,
                                scheduled_meeting_time=suggested_time,
                                contact=contact,
                                event='Meeting',  # Set event type
                                last_seen=last_meeting_time  # Set last_seen to last meeting time
                            )
                    else:
                        logger.info(f"Conditions not met. Time since last meeting: {time_since_last_meeting}, Frequency: {frequency}")
                else:
                    logger.info(f"Creating notification for {user.username}")
                    message = f"You haven't met {contact.name} from your {group.name} group yet."
                    suggested_time = schedule_meeting_time(now, preferred_start_times, preferred_end_times, preferred_days)
                    if suggested_time:
                        Notification.objects.create(
                            user=user,
                            message=message,
                            contact=contact,
                            scheduled_meeting_time=suggested_time,
                            event='Meeting',  # Set event type
                            last_seen=None  # No last meeting, so set last_seen to None
                        )
            else:
                logger.info(f"No settings found for {user.username} and {group.name}")

def schedule_meeting_time(now, preferred_start_times, preferred_end_times, preferred_days):
    if timezone.is_naive(now):
        now = timezone.make_aware(now, timezone.get_current_timezone())

    valid_days = [day[0] for day in DAYS_OF_WEEK]
    preferred_days = [day for day in preferred_days if day in valid_days]

    if not preferred_days:
        raise ValueError("Preferred days list is empty after filtering")

    random.shuffle(preferred_days)

    for preferred_day in preferred_days:
        for week_offset in [0, 1]:
            try:
                index = valid_days.index(preferred_day)
                days_until = (7 * week_offset + index - now.weekday()) % 7
                next_preferred_day = now + timedelta(days=days_until)
                preferred_start_time = preferred_start_times[preferred_day]
                preferred_end_time = preferred_end_times[preferred_day]

                start_hour = preferred_start_time.hour
                end_hour = preferred_end_time.hour

                if start_hour > end_hour:
                    raise ValueError("Preferred start time is later than end time")

                max_hour = end_hour - 1

                if start_hour > max_hour:
                    continue

                random_hour = random.randint(start_hour, max_hour)
                possible_minutes = [0, 15, 30]

                if random_hour == max_hour:
                    random_minute = random.choice(possible_minutes)
                else:
                    random_minute = random.choice([0, 15, 30, 45])

                suggested_time = datetime.combine(
                    next_preferred_day.date(),
                    time(hour=random_hour, minute=random_minute)
                )
                suggested_time = timezone.make_aware(suggested_time, timezone.get_current_timezone())

                return suggested_time

            except ValueError as e:
                continue

    raise ValueError("No valid preferred days found")