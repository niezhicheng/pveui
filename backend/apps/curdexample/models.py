from django.db import models
from apps.common.models import BaseAuditModel


class Example(BaseAuditModel):
    """示例业务模型：用于演示 CRUD、审计字段与数据权限基座。"""

    name = models.CharField(max_length=64, verbose_name='名称')
    description = models.CharField(max_length=255, blank=True, default='', verbose_name='描述')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='价格')
    is_active = models.BooleanField(default=True, verbose_name='启用')

    class Meta:
        verbose_name = '示例'
        verbose_name_plural = '示例'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self) -> str:
        return self.name
