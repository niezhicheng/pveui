"""操作日志模型：记录系统操作行为。"""

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models


class OperationLog(models.Model):
    """操作日志模型：记录用户的操作行为。

    记录字段：
    - 操作人、操作时间
    - 操作类型（create/update/delete/view 等）
    - 操作对象（content_type, object_id）
    - 请求信息（路径、方法、IP、参数）
    - 响应状态、错误信息
    - 浏览器信息
    """

    # 操作类型选择
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_VIEW = 'view'
    ACTION_LIST = 'list'
    ACTION_OTHER = 'other'

    ACTION_CHOICES = [
        (ACTION_CREATE, '创建'),
        (ACTION_UPDATE, '更新'),
        (ACTION_DELETE, '删除'),
        (ACTION_VIEW, '查看'),
        (ACTION_LIST, '列表'),
        (ACTION_OTHER, '其他'),
    ]

    # 操作人信息
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_logs',
        verbose_name='操作人',
    )
    username = models.CharField(max_length=150, blank=True, default='', verbose_name='用户名（冗余）')

    # 操作时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间', db_index=True)

    # 操作类型
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        default=ACTION_OTHER,
        verbose_name='操作类型',
        db_index=True,
    )

    # 操作对象（使用 ContentType 支持任意模型）
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='对象类型',
    )
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='对象ID')
    object_repr = models.CharField(max_length=255, blank=True, default='', verbose_name='对象描述')

    # 请求信息
    request_path = models.CharField(max_length=500, blank=True, default='', verbose_name='请求路径')
    request_method = models.CharField(max_length=10, blank=True, default='', verbose_name='请求方法')
    request_params = models.JSONField(default=dict, blank=True, verbose_name='请求参数')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    user_agent = models.CharField(max_length=500, blank=True, default='', verbose_name='浏览器信息')

    # 响应信息
    status_code = models.IntegerField(null=True, blank=True, verbose_name='响应状态码')
    error_message = models.TextField(blank=True, default='', verbose_name='错误信息')

    # 备注
    remark = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')

    class Meta:
        verbose_name = '操作日志'
        verbose_name_plural = '操作日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['request_path', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
        ]

    def __str__(self):
        return f'{self.username or "匿名"} - {self.get_action_type_display()} - {self.object_repr or self.request_path} - {self.created_at}'

