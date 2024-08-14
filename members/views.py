from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout 
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.forms import modelformset_factory
from django.template import loader
from django.utils import timezone
from django.contrib import messages
from .models import SignupForm, LoginForm, Contact, Group, Profile, Notification, UserSettings, Meeting, TimeRange, UserTimeRange
from .forms import ContactForm, ProfileForm, UserSettingsForm, TimeRangeForm, DailyTimeRangeForm, GroupFrequencyForm 
import json
from .constants import DAYS_OF_WEEK
from datetime import timedelta, datetime
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q
from django import forms
from collections import defaultdict
from django.middleware.csrf import get_token 

#PROFILE FUNCTIONS

@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "There was an error updating your profile. Please check the form and try again.")
    else:
        form = ProfileForm(instance=profile)
        form.fields['birthday'].widget = forms.DateInput(attrs={'type': 'date'})
    
    return render(request, 'profile.html', {
        'profile': profile,
        'form': form
    })

#CONNECT FUNCTIONS

@login_required
def connect(request):
    unread_notifications = Notification.objects.filter(user=request.user, read=False).select_related('contact')
    read_notifications = Notification.objects.filter(user=request.user, read=True).select_related('contact')
    for notification in unread_notifications:
        if notification.contact.birthday and notification.contact.birthday == timezone.now().date():
            notification.event = 'Birthday'
        else:
            notification.event = 'Meeting'
        notification.save()
    context = {
        'unread_notifications': unread_notifications,
        'read_notifications': read_notifications,
    }
    return render(request, 'connect.html', context)

@login_required
def mark_as_read(request):
    if request.method == "POST":
        if 'action' in request.POST:
            action = request.POST['action']
            
            if action == 'mark_as_read':
                # Mark selected notifications as read
                notification_ids = request.POST.getlist('notification_ids')
                notifications_read = Notification.objects.filter(id__in=notification_ids, user=request.user)
                for notification in notifications_read:
                    notification.mark_as_read()
                messages.success(request, "Selected notifications marked as read.")

            elif action == 'mark_all_as_read':
                # Mark all unread notifications as read
                unread_notifications = Notification.objects.filter(user=request.user, read=False)
                for notification in unread_notifications:
                    notification.mark_as_read()
                messages.success(request, "All notifications marked as read.")

        return redirect("connect")
    
    return render(request, 'connect.html', {
        'unread_notifications': Notification.objects.filter(user=request.user, read=False),
        'read_notifications': Notification.objects.filter(user=request.user, read=True),
    })

@login_required
def notification_detail(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    if not notification.read:
        notification.read = True
        notification.save()

    contact = notification.contact
    groups = contact.groups.all() if contact else []

    # Set the meeting duration to 1 hour
    meeting_duration = timedelta(hours=1)

    # Calculate the end time if scheduled_meeting_time exists
    scheduled_meeting_time = notification.scheduled_meeting_time
    if scheduled_meeting_time:
        end_time = scheduled_meeting_time + meeting_duration
    else:
        end_time = None

    context = {
        'notification': notification,
        'contact': contact,
        'groups': groups,
        'scheduled_meeting_time': scheduled_meeting_time,
        'end_time': end_time,  # Pass the end time to the context
    }
    return render(request, 'notification_detail.html', context)

@login_required
def reset_time_range(request, day):
    user_settings_list = UserSettings.objects.filter(user=request.user)
    for settings in user_settings_list:
        UserTimeRange.objects.filter(usersettings=settings, timerange__day=day).delete()
    return redirect('user_settings')

#GROUP FUNCTIONS

@login_required
def groups(request):
    groups = Group.objects.filter(user=request.user)
    group_count = groups.count()
    return render(request, 'groups.html', {'groups': groups, 'group_count': group_count})

@login_required
def add_group(request):
    if request.method == "POST":
        name = request.POST.get('name')
        if name:
            Group.objects.create(user=request.user, name=name)
            return redirect('groups')
    return render(request, 'add_group.html')

@login_required
def group_detail(request, pk):
    group = get_object_or_404(Group, pk=pk, user=request.user)
    query = request.GET.get('q', '')
    contacts = group.contacts.filter(user=request.user)

    if query:
        contacts = contacts.filter(Q(name__icontains=query))

    group_people_count = contacts.count()
    grouped_contacts = {}
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        grouped_contacts[letter] = contacts.filter(name__istartswith=letter)

    return render(request, 'group_detail.html', {
        'group': group,
        'contacts': contacts,
        'group_people_count': group_people_count,
        'query': query,
        'grouped_contacts': grouped_contacts
    })
    
@login_required
def delete_group(request, pk):
    group = get_object_or_404(Group, pk=pk, user=request.user)
    if request.method == "POST":
        group.delete()
        return redirect('groups')
    return render(request, "delete_group.html", {'group': group})


#CALENDAR FUNCTIONS

from django.utils import timezone

@login_required
def calendar(request):
    user = request.user
    now = timezone.now()
    
    # Fetch only future meetings for display
    future_meetings = Meeting.objects.filter(user=user, scheduled_time__gte=now).order_by('scheduled_time')

    events = [{
        'title': f'Meeting with {meeting.person_met.name} at {meeting.location}',
        'start': meeting.scheduled_time.isoformat(),  # Use scheduled_time for event start
        'end': (meeting.scheduled_time + timedelta(hours=1)).isoformat(),  # Assuming 1 hour duration
        'color': 'red'  # You can customize the color
    } for meeting in future_meetings]

    upcoming_meetings = future_meetings[:3]  # Display the next 3 upcoming meetings

    context = {
        'events_json': json.dumps(events),
        'upcoming_meetings': upcoming_meetings
    }
    return render(request, 'calendar.html', context)


@login_required
def delete_meeting(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id, user=request.user)
    if request.method == 'POST':
        meeting.delete()
        messages.success(request, "Meeting successfully deleted.")
        return redirect('calendar')  # Redirect to the calendar page
    
    return redirect('calendar')  # In case of a GET request or any other method, just redirect

@login_required
def day_calendar(request, date):
    user = request.user
    selected_date = datetime.strptime(date, '%Y-%m-%d').date()

    # Fetch meetings for the selected date
    start_of_day = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()), timezone.get_current_timezone())
    end_of_day = timezone.make_aware(datetime.combine(selected_date, datetime.max.time()), timezone.get_current_timezone())
    meetings = Meeting.objects.filter(user=user, scheduled_time__range=(start_of_day, end_of_day)).order_by('scheduled_time')

    events = [{
        'title': f'Meeting with {meeting.person_met.name} at {meeting.location}',
        'start': meeting.scheduled_time.isoformat(),
        'end': (meeting.scheduled_time + timedelta(hours=1)).isoformat(),  # Assuming 1 hour duration
        'color': 'red',  # Highlight the meeting in red
        'id': meeting.id  # Include the meeting id
    } for meeting in meetings]

    context = {
        'selected_date': selected_date.strftime('%Y-%m-%d'),
        'events': json.dumps(events),
        'csrf_token': get_token(request),  # Ensure CSRF token is passed to the template
    }
    return render(request, 'day_calendar.html', context)

#AUTHENTICATION FUNCTIONS

def user_signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)    
                return redirect('main')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    return redirect('login')

#MAIN FUNCTIONS

@login_required(login_url='login')
def main(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    unread_notifications_count = Notification.objects.filter(user=request.user, read=False).count()
    
    context = {
        'unread_notifications_count': unread_notifications_count,
        'profile': profile,
    }
    return render(request, 'main.html', context)

#CONTACTS FUNCTIONS

@login_required
def contact_list(request):
    user = request.user
    contacts = Contact.objects.filter(user=user).prefetch_related('groups')
    contact_count = contacts.count()
    query = request.GET.get('q')  # Get the search query from the request

    if query:
        contacts = contacts.filter(
            Q(name__icontains=query) | Q(phone__icontains=query)
        ).order_by('name')
    else:
        contacts = contacts.order_by('name')

    grouped_contacts = {}
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        grouped_contacts[letter] = contacts.filter(name__istartswith=letter)

    return render(request, 'contacts.html', {
        'contacts': contacts,
        'contact_count': contact_count,
        'query': query,
        'grouped_contacts': grouped_contacts
    })

@login_required
def add_contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.user = request.user
            contact.save()
            form.save_m2m()
            return redirect('contacts')
        else:
            print(form.errors)  # Print form errors for debugging
    else:
        form = ContactForm(user=request.user)
    return render(request, 'add_contact.html', {'form': form})

@login_required
def delete_contact(request, pk):
    contact = get_object_or_404(Contact, pk=pk, user=request.user)
    if request.method == "POST":
        contact.delete()
        return redirect('contacts')
    return render(request, 'delete_contact.html', {'contact': contact})

@login_required
def edit_contact(request, pk):
    contact = get_object_or_404(Contact, pk=pk, user=request.user)
    if request.method == "POST":
        form = ContactForm(request.POST, request.FILES, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, "Contact details updated successfully.")
            return redirect('contact_details', pk=pk)
    else:
        form = ContactForm(instance=contact)
    return render(request, 'contact_details.html', {'form': form, 'contact': contact})

@login_required
def contact_details(request, pk):
    contact = get_object_or_404(Contact, pk=pk, user=request.user)
    source = request.GET.get('source', 'contacts')
    if request.method == "POST":
        form = ContactForm(request.POST, request.FILES, instance=contact, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Contact updated successfully.")
            return redirect('contact_details', pk=contact.pk)
    else:
        form = ContactForm(instance=contact, user=request.user)
        form.fields['birthday'].widget = forms.DateInput(attrs={'type': 'date'})
    return render(request, 'contact_details.html', {
        'contact': contact,
        'source': source,
        'form': form
    })

#USER_SETTINGS

@login_required
def user_settings(request):
    user = request.user

    # Fetch all groups related to the current user
    user_groups = Group.objects.filter(user=user)

    # Ensure UserSettings exists for all groups
    for group in user_groups:
        if not UserSettings.objects.filter(user=user, group=group).exists():
            UserSettings.objects.create(user=user, group=group, frequency=0)

    # Fetch all UserSettings instances for the current user
    user_settings_list = UserSettings.objects.filter(user=user)

    # Fetch general time ranges related to the current user
    general_time_ranges = {
        utr.timerange.day: utr.timerange
        for utr in UserTimeRange.objects.filter(usersettings__user=user)
    }

    # Initialize form for updating daily time ranges
    daily_time_range_form = DailyTimeRangeForm(request.POST or None)

    # Prepare dictionary to store group frequencies
    group_frequencies = {us.group.name: us.frequency for us in user_settings_list}

    if request.method == 'POST':
        if 'update_time_range' in request.POST and daily_time_range_form.is_valid():
            day = daily_time_range_form.cleaned_data['day']
            start_time = daily_time_range_form.cleaned_data['start_time']
            end_time = daily_time_range_form.cleaned_data['end_time']

            if start_time and end_time:
                if start_time > end_time:
                    daily_time_range_form.add_error(None, "Start time cannot be after end time.")
                else:
                    timerange, created = TimeRange.objects.get_or_create(
                        day=day,
                        start_time=start_time,
                        end_time=end_time,
                        defaults={'meeting_duration': 60}
                    )

                    UserTimeRange.objects.filter(usersettings__user=user, timerange__day=day).delete()

                    for user_settings in user_settings_list:
                        UserTimeRange.objects.create(
                            usersettings=user_settings,
                            timerange=timerange
                        )

            return redirect('user_settings')

        if 'reset_time_range' in request.POST:
            day_to_reset = request.POST.get('day_to_reset')
            if day_to_reset:
                UserTimeRange.objects.filter(usersettings__user=user, timerange__day=day_to_reset).delete()

        if 'update_frequency' in request.POST:
            group_id = request.POST.get('group')
            frequency = request.POST.get('frequency')

            if group_id and frequency is not None:
                group = Group.objects.get(id=group_id, user=user)
                user_settings, created = UserSettings.objects.get_or_create(user=user, group=group)
                user_settings.frequency = frequency
                user_settings.save()
                messages.success(request, f"Frequency for {group.name} updated to {frequency} days.")

                # Update the group frequencies dictionary after saving
                group_frequencies[group.name] = frequency

        return redirect('user_settings')

    context = {
        'time_range_form': daily_time_range_form,
        'user_settings_list': user_settings_list,
        'general_time_ranges': general_time_ranges,
        'days_of_week': DAYS_OF_WEEK,
        'user_groups': user_groups,
        'group_frequencies': group_frequencies,
    }

    return render(request, "user_settings.html", context)

#SCHEDULE MEETING FUNCTIONS

@login_required
def schedule_meeting(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
    except Notification.DoesNotExist:
        messages.error(request, "The notification you're trying to access no longer exists.")
        return redirect('connect')
    
    group = Group.objects.filter(user=request.user).first()

    # Filter meetings based on the notification's contact and group
    meetings = Meeting.objects.filter(
        user=request.user,
        group=group,
        person_met=notification.contact
    )

    if meetings.exists():
        # If there are multiple meetings, choose the most recent one or handle duplicates as needed
        meeting = meetings.latest('scheduled_time')
    else:
        # If no meeting exists, create a new one
        meeting = Meeting.objects.create(
            user=request.user,
            group=group,
            person_met=notification.contact,
            scheduled_time=notification.scheduled_meeting_time,
            location='Defined location'
        )

    if request.method == 'POST':
        if 'update_time' in request.POST:
            new_date_str = request.POST.get('new_date')
            new_time_str = request.POST.get('new_time')

            if new_date_str and new_time_str:
                try:
                    new_datetime_str = f"{new_date_str}T{new_time_str}"
                    new_scheduled_time = timezone.make_aware(datetime.strptime(new_datetime_str, '%Y-%m-%dT%H:%M'))
                    if new_scheduled_time < timezone.now():
                        messages.error(request, "Meeting time cannot be in the past.")
                        return redirect('schedule_meeting', notification_id=notification_id)
                    # Update the meeting's scheduled time
                    meeting.scheduled_time = new_scheduled_time
                    meeting.save()
                    messages.success(request, "Meeting time updated successfully.")
                except ValueError:
                    messages.error(request, "Invalid date or time entered.")
            else:
                messages.error(request, "Both date and time must be provided.")

            return redirect('schedule_meeting', notification_id=notification_id)

        elif 'confirm' in request.POST:
            messages.success(request, f"You have confirmed a meeting with {notification.contact.name}.")
            return redirect('calendar')

        elif 'cancel' in request.POST:
            meeting.delete()
            messages.success(request, "Meeting canceled successfully.")
            return redirect('calendar')

    scheduled_meeting_time = meeting.scheduled_time
    end_time = scheduled_meeting_time + meeting.duration

    context = {
        'scheduled_meeting_time': scheduled_meeting_time,
        'end_time': end_time,
        'notification_id': notification_id,
    }

    return render(request, 'schedule_meeting.html', context)


@login_required
def edit_meeting(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id, user=request.user)

    if request.method == 'POST':
        if 'update_time' in request.POST:
            new_date_str = request.POST.get('new_date')
            new_time_str = request.POST.get('new_time')
            new_location = request.POST.get('location')

            if new_date_str and new_time_str:
                try:
                    new_datetime_str = f"{new_date_str}T{new_time_str}"
                    new_scheduled_time = timezone.make_aware(datetime.strptime(new_datetime_str, '%Y-%m-%dT%H:%M'))
                    if new_scheduled_time < timezone.now():
                        messages.error(request, "Meeting time cannot be in the past.")
                        return redirect('edit_meeting', meeting_id=meeting_id)
                    # Update the meeting's scheduled time, location, and calculate the new end time
                    meeting.scheduled_time = new_scheduled_time
                    meeting.location = new_location
                    meeting.save()

                    messages.success(request, "Meeting updated successfully.")
                    return redirect('day_calendar', date=new_scheduled_time.date())
                except ValueError:
                    messages.error(request, "Invalid date or time entered.")
            else:
                messages.error(request, "Both date and time must be provided.")

    scheduled_meeting_time = meeting.scheduled_time
    end_time = scheduled_meeting_time + timedelta(hours=1)  # Ensure the end time is one hour after the start time

    context = {
        'meeting': meeting,
        'scheduled_meeting_time': scheduled_meeting_time,
        'end_time': end_time,
        'date': scheduled_meeting_time.date().strftime('%Y-%m-%d'),
    }

    return render(request, 'edit_meeting.html', context)
