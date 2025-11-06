"""Audit 应用配置。"""

from django.apps import AppConfig


class AuditConfig(AppConfig):
    """Audit 应用配置。"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audit'
    verbose_name = '操作日志'

