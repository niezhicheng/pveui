"""通用抽象模型：审计与归属信息。

供业务模型继承，不需要单独注册 app/migration（抽象类）。

包含：
- created_at / updated_at 时间戳
- created_by / updated_by 用户
- owner_organization 归属组织（引用 rbac.Organization）
- is_deleted 软删除标记（可选配合 SoftDeleteMixin 使用）
- remark 备注
"""

from django.conf import settings
from django.db import models


class BaseAuditModel(models.Model):
    """审计与归属字段抽象基类。"""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_created',
        verbose_name='创建人',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_updated',
        verbose_name='更新人',
    )

    owner_organization = models.ForeignKey(
        'rbac.Organization',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_owned',
        verbose_name='归属组织',
    )

    is_deleted = models.BooleanField(default=False, verbose_name='已删除')
    remark = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['owner_organization']),
            models.Index(fields=['is_deleted']),
        ]


