from django.contrib import admin
from .models import Blog


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'source', 'read_time', 'created_at')
    list_filter = ('category', 'source', 'created_at')
    search_fields = ('title', 'summary', 'content', 'source')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Article Content', {
            'fields': ('title', 'summary', 'content', 'category')
        }),
        ('Origin & Link', {
            'fields': ('source', 'link', 'read_time', 'author')
        }),
        ('Visuals', {
            'fields': ('image_url', 'image_name')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
