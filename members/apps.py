from django.apps import AppConfig

class MembersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'members'

class ContactsConfig(AppConfig):
    name = 'contacts'

    def ready(self):
        import members.signals
