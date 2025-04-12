from django.apps import AppConfig


class ContentGenerationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'content_generation'
    verbose_name = 'Content Generation'

    def ready(self):
        """Initialize app when Django starts"""
        # Import any signals here if needed
        # Example: import content_generation.signals
        pass