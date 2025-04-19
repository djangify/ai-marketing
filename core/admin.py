from django.contrib import admin
from .models import Tag, TaggedItem

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    list_filter = ('user',)
    search_fields = ('name',)

@admin.register(TaggedItem)
class TaggedItemAdmin(admin.ModelAdmin):
    list_display = ('tag', 'content_type', 'object_id')
    list_filter = ('tag', 'content_type')