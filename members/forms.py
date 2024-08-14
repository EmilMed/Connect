# contacts/forms.py
from django import forms
from .constants import DAYS_OF_WEEK
from .models import Contact, Group, Profile, UserSettings, TimeRange, UserTimeRange
from django.utils.translation import gettext_lazy as _
import json

class ContactForm(forms.ModelForm):
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'placeholder': 'Enter your phone number'}))

    class Meta:
        model = Contact
        fields = ['name', 'phone', 'hobbies', 'birthday', 'food', 'picture', 'groups']
        widgets = {'birthday': forms.DateInput(attrs={'type': 'date'})}
        
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), widget=forms.CheckboxSelectMultiple, required=False)
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ContactForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['groups'].queryset = Group.objects.filter(user=user)

class ProfileForm(forms.ModelForm):
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'placeholder': 'Enter your phone number'}))
    class Meta:
        model = Profile
        fields = ['image', 'name', 'phone', 'hobbies', 'birthday', 'food']
        widgets = {'birthday': forms.DateInput(attrs={'type': 'date'})}

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['group', 'frequency']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(UserSettingsForm, self).__init__(*args, **kwargs)
        self.fields['group'].queryset = Group.objects.filter(user=user)

class TimeRangeForm(forms.ModelForm):
    class Meta:
        model = TimeRange
        fields = ['day', 'start_time', 'end_time']
        widgets = {
            'day': forms.Select(choices=DAYS_OF_WEEK),
            'start_time': forms.TimeInput(format='%H:%M'),
            'end_time': forms.TimeInput(format='%H:%M'),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("Start time must be before end time.")

        return cleaned_data

class DailyTimeRangeForm(forms.Form):
    day = forms.ChoiceField(choices=DAYS_OF_WEEK, widget=forms.Select(attrs={'class': 'form-control'}))
    start_time = forms.TimeField(required=False, widget=forms.TimeInput(format='%H:%M', attrs={'class': 'form-control'}))
    end_time = forms.TimeField(required=False, widget=forms.TimeInput(format='%H:%M', attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("Start time must be before end time.")
        elif start_time or end_time:
            raise forms.ValidationError("Both start time and end time must be provided.")

        return cleaned_data
    
class GroupFrequencyForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super(GroupFrequencyForm, self).__init__(*args, **kwargs)
        
        # Get all groups for the current user
        user_settings_list = UserSettings.objects.filter(user=user)
        
        # Dynamically add a form field for each group
        for user_settings in user_settings_list:
            self.fields[user_settings.group.name] = forms.CharField(label=user_settings.group.name, required=False)