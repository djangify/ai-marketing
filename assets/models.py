# assets/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid


class Asset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='client_assets')
    title = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    file_url = models.URLField(max_length=1000)
    file_type = models.CharField(max_length=50, choices=[
        ('text', 'Text'),
        ('markdown', 'Markdown'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('other', 'Other')
    ])
    mime_type = models.CharField(max_length=100)
    size = models.BigIntegerField()
    content = models.TextField(blank=True, default='')
    token_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title


class AssetProcessingJob(models.Model):
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('max_attempts_exceeded', 'Max Attempts Exceeded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name='processing_job')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='asset_jobs')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='created')
    error_message = models.TextField(blank=True, null=True)
    attempts = models.IntegerField(default=0)
    last_heart_beat = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Processing job for {self.asset.title}"
    