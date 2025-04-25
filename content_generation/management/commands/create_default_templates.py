from django.core.management.base import BaseCommand
from content_generation.models import PromptTemplate
from content_generation.prompt_enhancement import PromptEnhancer

class Command(BaseCommand):
    help = 'Creates default prompt templates if none exist'

    def handle(self, *args, **options):
        templates_count = PromptTemplate.objects.count()
        if templates_count > 0:
            self.stdout.write(self.style.WARNING(f'Found {templates_count} existing templates. Skipping creation.'))
            return
        
        self.stdout.write('Creating default prompt templates...')
        
        # Create general content template
        PromptTemplate.objects.create(
            name="General Content",
            content_type="general",
            system_prompt=PromptEnhancer.GENERAL_TEMPLATE,
            description="Default template for general content creation",
            is_active=True,
            is_default=True
        )
        self.stdout.write(self.style.SUCCESS('Created General Content template'))
        
        # Create blog post template
        PromptTemplate.objects.create(
            name="Blog Post",
            content_type="blog",
            system_prompt=PromptEnhancer.BLOG_TEMPLATE,
            description="Template optimized for blog post creation",
            is_active=True,
            is_default=True
        )
        self.stdout.write(self.style.SUCCESS('Created Blog Post template'))
        
        # Create social media template
        PromptTemplate.objects.create(
            name="Social Media",
            content_type="social",
            system_prompt=PromptEnhancer.SOCIAL_TEMPLATE,
            description="Template optimized for social media content",
            is_active=True,
            is_default=True
        )
        self.stdout.write(self.style.SUCCESS('Created Social Media template'))
        
        # Create email marketing template
        PromptTemplate.objects.create(
            name="Email Marketing",
            content_type="email",
            system_prompt=PromptEnhancer.EMAIL_TEMPLATE,
            description="Template optimized for email marketing content",
            is_active=True,
            is_default=True
        )
        self.stdout.write(self.style.SUCCESS('Created Email Marketing template'))
        
        self.stdout.write(self.style.SUCCESS('Successfully created all default prompt templates'))
        