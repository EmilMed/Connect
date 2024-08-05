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
from django.http import JsonResponse
from django.db.models import Q
from collections import defaultdict

#PROFILE FUNCTIONS

@login_required
def profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'profile.html', {
        'profile': profile,
        'form': form
    })

@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'edit_profile.html', {'form': form})

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
    if request.method == "POST" and 'action' in request.POST and request.POST['action'] == 'mark_as_read':
        notification_ids = request.POST.getlist('notification_ids')
        notifications_read = Notification.objects.filter(id__in=notification_ids)
        for notification in notifications_read:
            notification.mark_as_read()
        messages.success(request, "Notifications marked as read")
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

def delete_meeting(request, meeting_id):
    if request.method == 'POST':
        meeting = get_object_or_404(Meeting, id=meeting_id)
        meeting.delete()
        messages.success(request, "Meeting successfully deleted.")
        return JsonResponse({'success': True, 'redirect_url': redirect('calendar').url})
    else:
        return JsonResponse({'success': False}, status=400)
    
from django.middleware.csrf import get_token 

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
                return redirect('members')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')

def members(request):
  return render(request, 'main.html')

#MAIN FUNCTIONS

@login_required
def main(request):
    unread_notifications_count = Notification.objects.filter(user=request.user, read=False).count()
    context = {
        'unread_notifications_count': unread_notifications_count,
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
        form = ContactForm(user=request.user)
    return render(request, 'add_contact.html', {'form': form})

@login_required
def delete_contact(request, pk):
    contact = get_object_or_404(Contact, pk=pk, user=request.user)
    if request.method == "POST":
        contact.delete()
        return redirect('contacts')
    return render(request, 'delete_contact.html', {'contact': contact})

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
    all_groups = Group.objects.filter(user=user)

    # Ensure UserSettings exists for all groups
    for group in all_groups:
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
    group_frequencies = {}
    for user_settings in user_settings_list:
        group_frequencies[user_settings.group.name] = user_settings.frequency

    # Initialize forms for updating group frequencies
    freq_forms = [
        UserSettingsForm(request.POST if request.method == 'POST' else None, instance=user_settings, prefix=f'freq_{user_settings.id}')
        for user_settings in user_settings_list
    ]

    if request.method == 'POST':
        if 'update_time_range' in request.POST and daily_time_range_form.is_valid():
            day = daily_time_range_form.cleaned_data['day']
            start_time = daily_time_range_form.cleaned_data['start_time']
            end_time = daily_time_range_form.cleaned_data['end_time']

            if start_time and end_time:
                if start_time > end_time:
                    # Return an error message or handle appropriately
                    daily_time_range_form.add_error(None, "Start time cannot be after end time.")
                else:
                    timerange, created = TimeRange.objects.get_or_create(
                        day=day,
                        start_time=start_time,
                        end_time=end_time,
                        defaults={'meeting_duration': 60} 
                    )

                    # Delete existing UserTimeRange entries for the specific day
                    UserTimeRange.objects.filter(usersettings__user=user, timerange__day=day).delete()

                    # Create or update UserTimeRange for each UserSettings
                    for user_settings in user_settings_list:
                        user_time_range, created = UserTimeRange.objects.get_or_create(
                            usersettings=user_settings,
                            timerange=timerange
                        )
                        user_time_range.timerange = timerange
                        user_time_range.save()

            return redirect('user_settings')

        if 'reset_time_range' in request.POST:
            day_to_reset = request.POST.get('day_to_reset')
            if day_to_reset:
                UserTimeRange.objects.filter(usersettings__user=user, timerange__day=day_to_reset).delete()
                return redirect('user_settings')

        # Handle frequency form submission
        for form in freq_forms:
            if form.is_valid():
                form.save()
                # Update the group frequencies dictionary after saving the form
                group_frequencies[form.instance.group.name] = form.cleaned_data['frequency']
            else:
                print(f"Form invalid for group {form.instance.group.name}")

        return redirect('user_settings')

    # Prepare context for rendering the template
    context = {
        'time_range_form': daily_time_range_form,
        'freq_forms': freq_forms,
        'user_settings_list': user_settings_list,
        'general_time_ranges': general_time_ranges,
        'days_of_week': DAYS_OF_WEEK,
        'group_frequencies': group_frequencies,
    }

    return render(request, "user_settings.html", context)

#SCHEDULE MEETING FUNCTIONS

def schedule_meeting(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    group = Group.objects.filter(user=request.user).first()
    contact = notification.contact

    # Calculate the end time based on a predefined meeting duration
    meeting_duration = timedelta(hours=1)
    scheduled_meeting_time = notification.scheduled_meeting_time
    if timezone.is_naive(scheduled_meeting_time):
        scheduled_meeting_time = timezone.make_aware(scheduled_meeting_time, timezone.get_current_timezone())
    end_time = scheduled_meeting_time + meeting_duration if scheduled_meeting_time else None

    if request.method == 'POST':
        if 'confirm' in request.POST:
            # Log the data being saved
            print(f"Creating meeting: user={request.user}, group={group}, contact={contact}, scheduled_time={scheduled_meeting_time}")
            if scheduled_meeting_time < timezone.now():
                messages.error(request, "You cannot schedule a meeting in the past.")
                return redirect('notification_detail', notification_id=notification_id)


            # Create a new Meeting object with scheduled_time set
            Meeting.objects.create(
                user=request.user,
                group=group,
                person_met=contact,
                scheduled_time=scheduled_meeting_time,  # Use this field for the actual meeting time
                timestamp=timezone.now(),
                location='Defined location'  # Assume location is defined here or taken from another input
            )
            messages.success(request, f"You have confirmed a meeting with {contact.name} on {scheduled_meeting_time.strftime('%Y-%m-%d %H:%M')}.")
            return redirect('calendar')
        
        elif 'update_time' in request.POST:
            # Retrieve the updated meeting time from the form
            new_date_str = request.POST.get('new_date')
            new_time_str = request.POST.get('new_time')
            new_datetime_str = f"{new_date_str}T{new_time_str}"
            new_scheduled_time = timezone.make_aware(datetime.strptime(new_datetime_str, '%Y-%m-%dT%H:%M'))

            # Update the notification with the new scheduled time
            notification.scheduled_meeting_time = new_scheduled_time
            notification.save()

            messages.success(request, "Meeting time updated successfully.")
            return redirect('schedule_meeting', notification_id=notification_id)  # Corrected redirect here
        
        elif 'cancel' in request.POST:
            return redirect('notification_detail', notification_id=notification_id)

    # Prepare meetings data for debugging or display purposes
    meetings = Meeting.objects.filter(user=request.user).order_by('timestamp')
    meetings_data = [
        {
            'title': f"{meeting.user.username} met {meeting.person_met.name} at {meeting.group.name}",
            'start': meeting.scheduled_time.strftime('%Y-%m-%dT%H:%M:%S') if meeting.scheduled_time else 'No scheduled time',
            'end': (meeting.scheduled_time + meeting_duration).strftime('%Y-%m-%dT%H:%M:%S') if meeting.scheduled_time else 'No end time'
        }
        for meeting in meetings
    ]

    context = {
        'notification': notification,
        'scheduled_meeting_time': scheduled_meeting_time,
        'end_time': end_time,
        'notification_id': notification_id,
        'meetings_data': json.dumps(meetings_data)
    }

    return render(request, 'schedule_meeting.html', context)