# content_generation/management/commands/create_default_ai_config.py
from django.core.management.base import BaseCommand
from content_generation.models import AIConfig

class Command(BaseCommand):
    help = 'Creates default AI configuration if none exists'

    def handle(self, *args, **options):
        if not AIConfig.objects.exists():
            AIConfig.objects.create(
                name="Default High-Quality Config",
                model_name="gpt-4o",
                fallback_model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=4000,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('Created default AI configuration'))
        else:
            # Update existing configuration if needed
            default_config = AIConfig.objects.filter(is_active=True).first()
            if default_config and default_config.model_name != "gpt-4o":
                default_config.model_name = "gpt-4o"
                default_config.fallback_model = "gpt-4o-mini"
                default_config.save()
                self.stdout.write(self.style.SUCCESS('Updated AI configuration to use GPT-4o'))
            else:
                self.stdout.write(self.style.SUCCESS('Default AI configuration already exists'))