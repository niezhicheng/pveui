"""知识库模型。"""

from django.db import models
from apps.common.models import BaseAuditModel


class KnowledgeArticle(BaseAuditModel):
    """知识库文章。"""

    CATEGORY_CHOICES = [
        ('guide', '使用指南'),
        ('faq', '常见问题'),
        ('troubleshooting', '故障排查'),
        ('other', '其他'),
    ]

    title = models.CharField(max_length=200, verbose_name='标题')
    summary = models.CharField(max_length=500, blank=True, default='', verbose_name='摘要')
    content = models.TextField(blank=True, default='', verbose_name='内容')
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='guide', verbose_name='分类')
    tags = models.CharField(max_length=255, blank=True, default='', verbose_name='标签', help_text='逗号分隔')
    is_published = models.BooleanField(default=True, verbose_name='已发布')
    is_pinned = models.BooleanField(default=False, verbose_name='置顶')

    class Meta:
        verbose_name = '知识库文章'
        verbose_name_plural = '知识库文章'
        ordering = ['-is_pinned', '-is_published', '-updated_at', '-id']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_published']),
            models.Index(fields=['is_pinned']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        return self.title


