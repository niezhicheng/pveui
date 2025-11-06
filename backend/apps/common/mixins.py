"""DRF 混入：自动填充审计与归属信息、可选软删除。"""

from typing import Any
from django.db import models
from rest_framework import viewsets


def _model_has_field(model: type[models.Model], field_name: str) -> bool:
    try:
        model._meta.get_field(field_name)  # type: ignore[attr-defined]
        return True
    except Exception:
        return False


def _get_user_primary_org(user: Any):
    """返回用户主组织（若存在）。延迟导入避免强耦合。"""
    try:
        from apps.rbac.models import UserOrganization  # 延迟导入
        return (
            UserOrganization.objects
            .filter(user=user, is_primary=True)
            .select_related('organization')
            .first()
        ).organization if user and getattr(user, 'is_authenticated', False) else None
    except Exception:
        return None


class AuditOwnerPopulateMixin(viewsets.GenericViewSet):
    """在 create/update 时自动填充 created_by/updated_by/owner_organization。"""

    def perform_create(self, serializer):  # noqa: D401
        model = serializer.Meta.model  # type: ignore[attr-defined]
        extra = {}
        user = getattr(self.request, 'user', None)
        if user and getattr(user, 'is_authenticated', False):
            if _model_has_field(model, 'created_by'):
                extra['created_by'] = user
            if _model_has_field(model, 'updated_by'):
                extra['updated_by'] = user
            if _model_has_field(model, 'owner_organization') and not serializer.validated_data.get('owner_organization'):
                org = _get_user_primary_org(user)
                if org is not None:
                    extra['owner_organization'] = org
        serializer.save(**extra)

    def perform_update(self, serializer):  # noqa: D401
        model = serializer.Meta.model  # type: ignore[attr-defined]
        extra = {}
        user = getattr(self.request, 'user', None)
        if user and getattr(user, 'is_authenticated', False):
            if _model_has_field(model, 'updated_by'):
                extra['updated_by'] = user
        serializer.save(**extra)


class SoftDeleteMixin(viewsets.GenericViewSet):
    """可选软删除：若模型包含 is_deleted 字段，则 destroy 改为软删除，并在查询时自动排除已删除数据。"""

    def get_queryset(self):  # noqa: D401
        queryset = super().get_queryset()
        try:
            model = queryset.model  # type: ignore[attr-defined]
        except Exception:
            return queryset
        if _model_has_field(model, 'is_deleted'):
            return queryset.filter(is_deleted=False)
        return queryset

    def perform_destroy(self, instance):  # noqa: D401
        if _model_has_field(instance.__class__, 'is_deleted'):
            setattr(instance, 'is_deleted', True)
            instance.save(update_fields=['is_deleted'])
        else:
            super().perform_destroy(instance)


