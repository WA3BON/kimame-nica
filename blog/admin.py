from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext as _g, gettext_lazy as _
from .models import Post, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('thumbnail_preview', 'title', 'author', 'is_published', 'published_at', 'updated_at')
    list_display_links = ('thumbnail_preview', 'title')
    list_editable = ('is_published',)
    list_filter = ('is_published', 'tags')
    search_fields = ('title', 'content')
    filter_horizontal = ('tags',)
    prepopulated_fields = {}
    readonly_fields = ('published_at', 'updated_at', 'thumbnail_preview')
    fields = ('title', 'slug', 'excerpt', 'content', 'thumbnail', 'thumbnail_preview', 'tags', 'author', 'is_published', 'published_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="height:50px;border-radius:4px;">', obj.thumbnail.url)
        return _g('(画像なし)')
    thumbnail_preview.short_description = _('サムネイル')
