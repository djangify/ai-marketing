# prompt_generator/admin.py
from django.contrib import admin
from .models import GeneratorCategory, GeneratorTemplate, GeneratorParameter, GeneratedPrompt

class GeneratorParameterInline(admin.TabularInline):
    model = GeneratorParameter
    extra = 1

@admin.register(GeneratorCategory)
class GeneratorCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

@admin.register(GeneratorTemplate)
class GeneratorTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_featured', 'is_active', 'created_at')
    list_editable = ('is_featured', 'is_active')  # Add this line
    list_filter = ('category', 'is_featured', 'is_active')
    search_fields = ('name', 'description', 'template_text')
    inlines = [GeneratorParameterInline]

@admin.register(GeneratorParameter)
class GeneratorParameterAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'template', 'parameter_type', 'is_required', 'order')
    list_filter = ('template', 'parameter_type', 'is_required')
    search_fields = ('name', 'display_name', 'description')

@admin.register(GeneratedPrompt)
class GeneratedPromptAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'template', 'token_count', 'created_at')
    list_filter = ('template', 'created_at')
    search_fields = ('name', 'prompt_text', 'user__username')
    readonly_fields = ('token_count', 'created_at')