# essay/apps.py
from django.apps import AppConfig


class EssayConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'essay'
    
    def ready(self):
        # Don't access database here - it causes warnings
        # Instead, create languages through a management command or migration
        pass
    # essay/apps.py


class EssayConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'essay'
    
    def ready(self):
        # Comment this out temporarily until we fix the model registration
        # import essay.signals
        pass