# essay/apps.py
from django.apps import AppConfig


class EssayConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'essay'
    
    def ready(self):
        # Import signals
        import essay.signals