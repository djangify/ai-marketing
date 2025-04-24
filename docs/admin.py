# docs/admin.py
from django.contrib import admin
from django import forms
from django.db import models
from .models import DocumentationCategory, DocumentationPage


# Step 1: Create a custom form
class DocumentationPageAdminForm(forms.ModelForm):
    class Meta:
        model = DocumentationPage
        fields = '__all__'
        widgets = {
            'content': forms.Textarea(attrs={'class': 'tinymce'}),
        }

    class Media:
        js = [
            "https://cdn.tiny.cloud/1/un8zow1xkkig1b5u22a9c87leiaqptdawjb1glbheshusyz1/tinymce/6/tinymce.min.js",
            "js/tinymce_init.js",  # Optional JS file to configure TinyMCE
        ]


# Step 2: Use the form in your ModelAdmin
@admin.register(DocumentationCategory)
class DocumentationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_editable = ('order',)


@admin.register(DocumentationPage)
class DocumentationPageAdmin(admin.ModelAdmin):
    form = DocumentationPageAdminForm
    list_display = ('title', 'category', 'order', 'is_published', 'updated_at')
    list_filter = ('category', 'is_published')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')
    list_editable = ('order', 'is_published')
    date_hierarchy = 'updated_at'
