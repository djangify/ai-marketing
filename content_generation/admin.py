from django.contrib import admin
from .models import ContentGenerationJob, AIConfig

@admin.register(ContentGenerationJob)
class ContentGenerationJobAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'status', 'started_at', 'completed_at', 'prompts_completed', 'prompts_total')
    list_filter = ('status', 'started_at', 'completed_at')
    search_fields = ('project__title', 'user__username', 'user__email')
    readonly_fields = ('id', 'started_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

@admin.register(AIConfig)
class AIConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_name', 'fallback_model', 'temperature', 'max_tokens', 'is_active')
    list_filter = ('is_active', 'model_name')
    search_fields = ('name', 'model_name')
    readonly_fields = ('id',)