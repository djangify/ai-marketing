# docs/admin.py
from django.contrib import admin
from .models import DocumentationCategory, DocumentationPage

@admin.register(DocumentationCategory)
class DocumentationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_editable = ('order',)

@admin.register(DocumentationPage)
class DocumentationPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'order', 'is_published', 'updated_at')
    list_filter = ('category', 'is_published')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')
    list_editable = ('order', 'is_published')
    date_hierarchy = 'updated_at'