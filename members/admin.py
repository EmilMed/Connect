from django.contrib import admin
from .models import Profile, Contact, Group, TimeRange, UserSettings, UserTimeRange

# Register other models
admin.site.register(Profile)
admin.site.register(Contact)
admin.site.register(Group)
admin.site.register(TimeRange)

class UserTimeRangeInline(admin.TabularInline):
    model = UserTimeRange
    extra = 1

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    inlines = [UserTimeRangeInline]
    list_display = ['user', 'group', 'frequency']

@admin.register(UserTimeRange)
class UserTimeRangeAdmin(admin.ModelAdmin):
    list_display = ['usersettings', 'timerange']
    raw_id_fields = ['usersettings', 'timerange']
