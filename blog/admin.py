from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import Category, Post

# Step 1: Custom form with TinyMCE
class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'content': forms.Textarea(attrs={'class': 'tinymce'}),
        }

    class Media:
        js = [
            "https://cdn.tiny.cloud/1/un8zow1xkkig1b5u22a9c87leiaqptdawjb1glbheshusyz1/tinymce/6/tinymce.min.js",
            "js/tinymce_init.js",  # Optional, you can configure this
        ]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


# Step 2: Use the form in PostAdmin
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm  # 🪄 Use the custom form here

    list_display = ('title', 'category', 'status', 'featured', 'publish_date', 'display_image')
    list_filter = ('status', 'featured', 'category', 'publish_date')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'publish_date'
    readonly_fields = ('created', 'updated')

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'status', 'featured', 'publish_date')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Media', {
            'fields': ('image', 'external_image_url', 'youtube_url', 'thumbnail'),
            'classes': ('collapse',),
        }),
        ('Advertisement', {
            'fields': ('ad_type', 'ad_code', 'ad_image', 'ad_url'),
            'classes': ('collapse',),
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',),
        }),
    )

    def display_image(self, obj):
        if obj.get_image_url():
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                obj.get_image_url()
            )
        return "No image"
    display_image.short_description = 'Image'
