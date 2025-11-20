from django.contrib import admin

from .models import KnowledgeArticle


@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'category', 'is_published', 'is_pinned', 'created_at', 'updated_at']
    list_filter = ['category', 'is_published', 'is_pinned', 'created_at']
    search_fields = ['title', 'summary', 'content', 'tags']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


