"""系统设置模型。"""

from django.db import models
from apps.common.models import BaseAuditModel


class SystemSetting(BaseAuditModel):
    """系统设置模型：用于存储系统配置项，如 API Key、密钥等。"""
    
    key = models.CharField(max_length=100, unique=True, verbose_name='配置键', help_text='配置的唯一标识，如：ai_openai_api_key')
    value = models.TextField(blank=True, default='', verbose_name='配置值', help_text='配置的值，敏感信息会加密存储')
    description = models.CharField(max_length=255, blank=True, default='', verbose_name='描述', help_text='配置的说明')
    category = models.CharField(max_length=50, default='general', verbose_name='分类', help_text='配置分类，如：ai、email、storage等')
    is_encrypted = models.BooleanField(default=False, verbose_name='是否加密', help_text='是否对敏感信息进行加密存储')
    is_public = models.BooleanField(default=False, verbose_name='是否公开', help_text='是否在前端公开显示（非敏感配置）')
    
    class Meta:
        verbose_name = '系统设置'
        verbose_name_plural = '系统设置'
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['category']),
        ]
        ordering = ['category', 'key']
    
    def __str__(self) -> str:
        return f"{self.key} ({self.category})"

