"""聊天模块：员工间实时聊天功能。"""

from django.conf import settings
from django.db import models
from apps.common.models import BaseAuditModel


class ChatMessage(BaseAuditModel):
    """聊天消息模型。"""
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='发送者'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name='接收者'
    )
    content = models.TextField(verbose_name='消息内容')
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='已读时间')

    class Meta:
        verbose_name = '聊天消息'
        verbose_name_plural = '聊天消息'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'receiver']),
            models.Index(fields=['receiver', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.content[:50]}"
