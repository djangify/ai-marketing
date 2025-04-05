from django.db import models
from django.contrib.auth.models import User
import uuid

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class Asset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='assets')
    title = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    file_url = models.TextField()
    file_type = models.CharField(max_length=50)
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
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='processing_jobs')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True, null=True)
    attempts = models.IntegerField(default=0)
    last_heart_beat = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Job for {self.asset.title} ({self.status})"

class Prompt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='prompts')
    name = models.CharField(max_length=255)
    prompt = models.TextField(blank=True, null=True)
    token_count = models.IntegerField(default=0)
    order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['order']

class GeneratedContent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='generated_contents')
    name = models.CharField(max_length=255)
    result = models.TextField()
    order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['order']
        