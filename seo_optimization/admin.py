from django.contrib import admin
from .models import SEOAnalysis, KeywordTracking

@admin.register(SEOAnalysis)
class SEOAnalysisAdmin(admin.ModelAdmin):
    list_display = ('content', 'project', 'seo_score', 'readability_score', 'created_at')
    list_filter = ('project', 'created_at')
    search_fields = ('content__name', 'project__title', 'meta_description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(project__user=request.user)

@admin.register(KeywordTracking)
class KeywordTrackingAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'user', 'relevance_score', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('keyword', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)