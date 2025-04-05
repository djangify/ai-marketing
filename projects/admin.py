from django.contrib import admin
from .models import Project, Asset, AssetProcessingJob, Prompt, GeneratedContent

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'user__username', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

class AssetProcessingJobInline(admin.StackedInline):
    model = AssetProcessingJob
    extra = 0
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_heart_beat')

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'file_type', 'token_count', 'created_at')
    list_filter = ('file_type', 'created_at')
    search_fields = ('title', 'project__title', 'file_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [AssetProcessingJobInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(project__user=request.user)

@admin.register(AssetProcessingJob)
class AssetProcessingJobAdmin(admin.ModelAdmin):
    list_display = ('asset', 'project', 'status', 'attempts', 'created_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('asset__title', 'project__title', 'error_message')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_heart_beat')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(project__user=request.user)

@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'token_count', 'order', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'project__title', 'prompt')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(project__user=request.user)

@admin.register(GeneratedContent)
class GeneratedContentAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'order', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'project__title', 'result')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(project__user=request.user)