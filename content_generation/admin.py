from django.contrib import admin
from .models import ContentGenerationJob, AIConfig, PromptTemplate

@admin.register(ContentGenerationJob)
class ContentGenerationJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'user', 'status', 'prompts_completed', 'prompts_total', 'started_at', 'completed_at')
    list_filter = ('status', 'started_at')
    search_fields = ('project__title', 'user__username', 'error_message')
    readonly_fields = ('started_at', 'completed_at')

@admin.register(AIConfig)
class AIConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_name', 'fallback_model', 'temperature', 'max_tokens', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'content_type', 'is_active', 'is_default', 'user', 'created_at')
    list_filter = ('content_type', 'is_active', 'is_default')
    search_fields = ('name', 'description', 'system_prompt')
    fieldsets = (
        (None, {
            'fields': ('name', 'content_type', 'description')
        }),
        ('Template Settings', {
            'fields': ('system_prompt', 'is_active', 'is_default', 'user')
        }),
    )
    