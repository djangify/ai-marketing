# prompts/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid
from projects.models import Project

class Prompt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_prompts')
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
