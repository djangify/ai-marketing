from django.db import models
from django.contrib.auth.models import User
import uuid
from projects.models import Project, GeneratedContent

class SEOAnalysis(models.Model):
    """Model to store SEO analysis results for generated content"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.ForeignKey(GeneratedContent, on_delete=models.CASCADE, related_name='seo_analysis')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='seo_analyses')
    
    # SEO Metrics
    readability_score = models.FloatField(default=0)
    keyword_density = models.JSONField(default=dict)  # Store as {'keyword': percentage}
    suggested_keywords = models.JSONField(default=list)  # Store as list of keywords
    meta_description = models.TextField(blank=True)
    seo_score = models.IntegerField(default=0)  # Overall score out of 100
    improvement_suggestions = models.JSONField(default=list)  # Store as list of suggestions
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"SEO Analysis for {self.content.name}"
    
    class Meta:
        verbose_name = "SEO Analysis"
        verbose_name_plural = "SEO Analyses"


class KeywordTracking(models.Model):
    """Model to track keywords and their performance"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tracked_keywords')
    keyword = models.CharField(max_length=100)
    projects = models.ManyToManyField(Project, related_name='tracked_keywords')
    relevance_score = models.FloatField(default=0.0)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.keyword
    
    class Meta:
        unique_together = ('user', 'keyword')