# core/middleware.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from projects.models import GeneratedContent, Asset
from assets.utils import sanitize_content

@receiver(pre_save, sender=GeneratedContent)
def sanitize_generated_content(sender, instance, **kwargs):
    """Sanitize content before saving to the database"""
    if instance.result:
        instance.result = sanitize_content(instance.result)

@receiver(pre_save, sender=Asset)
def sanitize_asset_content(sender, instance, **kwargs):
    """Sanitize asset content before saving to the database"""
    if instance.content:
        instance.content = sanitize_content(instance.content)
        