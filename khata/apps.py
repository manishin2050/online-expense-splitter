from django.apps import AppConfig

class KhataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'khata'

    def ready(self):
        import khata.signals
