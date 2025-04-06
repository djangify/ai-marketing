from django.contrib import admin
from .models import Template, TemplatePrompt

class TemplatePromptInline(admin.TabularInline):
    model = TemplatePrompt
    extra = 1
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'user__username', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [TemplatePromptInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

@admin.register(TemplatePrompt)
class TemplatePromptAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'token_count', 'order', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'template__title', 'prompt')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(template__user=request.user)
    