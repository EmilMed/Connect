from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
import json
from .constants import DAYS_OF_WEEK
from datetime import timedelta

class SignupForm(UserCreationForm):
    class Meta:
        model = User 
        fields = ['username', 'password1', 'password2']

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default="default.jpg", upload_to="profile_pics")
    name = models.CharField(max_length=100, blank=True)
    phone = models.IntegerField(blank=True, null=True)
    hobbies = models.CharField(max_length=100, blank=True)
    birthday = models.DateField(blank=True, null=True, default=None)
    food = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f'{self.user.username} profile'

class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    groups = models.ManyToManyField('Group', related_name='contacts', blank=True)
    name = models.CharField(max_length=100, blank=True)
    phone = models.IntegerField(blank=True, null=True)
    hobbies = models.CharField(max_length=100, blank=True)
    birthday = models.DateField(null=True, blank=True)
    food = models.CharField(max_length=100, blank=True)
    picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.name

class Group(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Notification(models.Model):
    EVENT_CHOICES = [
        ('Birthday', 'Birthday'),
        ('Meeting', 'Meeting'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, blank=True, null=True)
    scheduled_meeting_time = models.DateTimeField(blank=True, null=True)
    event = models.CharField(max_length=100, choices=EVENT_CHOICES, default='Meeting')
    last_seen = models.DateTimeField(null=True, blank=True, default='Not seen yet')

    def __str__(self):
        return f'Notification for {self.user.username} - {self.event}'
    
    def mark_as_read(self):
        self.read = True
        self.save()
    
class TimeRange(models.Model):
    day = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    meeting_duration = models.IntegerField(default=60)

    class Meta:
        unique_together = ('day', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.start_time} - {self.end_time}"

class UserSettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey('Group', on_delete=models.CASCADE)
    frequency = models.IntegerField()
    preferred_time_ranges = models.ManyToManyField(TimeRange, through='UserTimeRange', related_name='user_settings_set')

    class Meta:
        unique_together = ('user', 'group')

    def __str__(self):
        return f"{self.user.username} - {self.group.name} - {self.frequency} days"

class UserTimeRange(models.Model):
    usersettings = models.ForeignKey(UserSettings, on_delete=models.CASCADE)
    timerange = models.ForeignKey(TimeRange, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('usersettings', 'timerange')
      
class Meeting(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    person_met = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='meetings_with')
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=100)
    scheduled_time = models.DateTimeField(blank=True, null=True)
    duration = models.DurationField(default=timedelta(hours=1))

    class Meta:
        unique_together = ('user', 'group', 'person_met', 'scheduled_time')

    def __str__(self):
        return f"{self.user.username} met {self.person_met.name} at {self.group.name} group"


class Recommendation(models.Model):
    RECOMMENDATION_TYPES = [
        ('Restaurant', 'Restaurant'),
        ('Entertainment', 'Entertainment'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contact = models.ForeignKey('Contact', on_delete=models.CASCADE)
    type = models.CharField(max_length=100, choices=RECOMMENDATION_TYPES)
    name = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type}: {self.name} for {self.contact.name}"