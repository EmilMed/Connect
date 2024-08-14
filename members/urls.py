from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('login/', views.user_login, name='login'),
    path('main/', views.main, name='main'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('connect/', views.connect, name='connect'),
    path('calendar/', views.calendar, name='calendar'),
    path('contacts/', views.contact_list, name='contacts'),
    path('contacts/add/', views.add_contact, name='add_contact'),
    path('contacts/<int:pk>/', views.delete_contact, name='delete_contact'),
    path('contacts/edit/<int:pk>/', views.edit_contact, name='edit_contact'),
    path('contacts/detail/<int:pk>/', views.contact_details, name='contact_details'),
    path('groups/', views.groups, name='groups'),
    path('add_group/', views.add_group, name='add_group'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
    path('groups/delete_group/<int:pk>/', views.delete_group, name='delete_group'),
    path('user_settings/', views.user_settings, name='user_settings'),
    path('notification_detail/<int:notification_id>/', views.notification_detail, name='notification_detail'),
    path('mark-as-read/', views.mark_as_read, name='mark_as_read'),
    path('reset_time_range/<str:day>/', views.reset_time_range, name='reset_time_range'),
    path('schedule_meeting/<int:notification_id>/', views.schedule_meeting, name='schedule_meeting'),
    path('edit_meeting/<int:meeting_id>/', views.edit_meeting, name='edit_meeting'),
    path('delete_meeting/<int:meeting_id>/', views.delete_meeting, name='delete_meeting'),
    path('day_calendar/<str:date>/', views.day_calendar, name='day_calendar'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)