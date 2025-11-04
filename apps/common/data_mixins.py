"""RBAC 相关的 ViewSet Mixins。

提供数据权限过滤功能。
"""

from typing import List, Optional
from django.db.models import Q, QuerySet
from django.db import models
from rest_framework import viewsets
from apps.rbac.models import Role, UserOrganization, Organization


class DataScopeFilterMixin(viewsets.GenericViewSet):
    """数据权限过滤 Mixin。
    
    根据用户角色的数据权限范围（data_scope）自动过滤 queryset。
    
    支持的数据权限范围：
    - ALL: 全部数据（不限制）
    - SELF: 仅本人数据（created_by=user）
    - DEPT: 本部门数据（owner_organization=用户主组织）
    - DEPT_AND_SUB: 本部门及下级（owner_organization在用户主组织及其子组织中）
    - CUSTOM: 自定义组织（owner_organization在角色指定的组织列表中）
    
    如果用户有多个角色，取最宽泛的数据权限：
    ALL > DEPT_AND_SUB > DEPT > CUSTOM > SELF
    
    使用方式：
        class MyViewSet(DataScopeFilterMixin, viewsets.ModelViewSet):
            # 需要继承 BaseAuditModel 或包含 owner_organization 和 created_by 字段
            pass
    """

    def get_queryset(self):
        """重写 get_queryset，应用数据权限过滤。"""
        queryset = super().get_queryset()
        user = self.request.user

        # 超级用户拥有所有数据权限
        if user.is_superuser:
            return queryset

        # 获取用户的所有角色及其数据权限
        user_roles = Role.objects.filter(user_roles__user=user).select_related().prefetch_related('custom_data_organizations')
        
        if not user_roles.exists():
            # 没有角色，只返回自己创建的数据
            return self._filter_by_self(queryset, user)

        # 获取最宽泛的数据权限
        data_scope, custom_orgs = self._get_broadest_data_scope(user_roles)
        
        # 根据数据权限范围过滤
        if data_scope == 'ALL':
            return queryset
        elif data_scope == 'SELF':
            return self._filter_by_self(queryset, user)
        elif data_scope == 'DEPT':
            return self._filter_by_dept(queryset, user)
        elif data_scope == 'DEPT_AND_SUB':
            return self._filter_by_dept_and_sub(queryset, user)
        elif data_scope == 'CUSTOM':
            return self._filter_by_custom(queryset, custom_orgs)
        else:
            # 默认只返回自己创建的数据
            return self._filter_by_self(queryset, user)

    def _get_broadest_data_scope(self, roles: QuerySet) -> tuple:
        """获取最宽泛的数据权限范围。
        
        Args:
            roles: 用户的所有角色
            
        Returns:
            tuple: (data_scope, custom_orgs)
                - data_scope: 最宽泛的数据权限范围
                - custom_orgs: 自定义组织列表（如果data_scope为CUSTOM）
        """
        # 优先级：ALL > DEPT_AND_SUB > DEPT > CUSTOM > SELF
        priority_map = {
            'ALL': 5,
            'DEPT_AND_SUB': 4,
            'DEPT': 3,
            'CUSTOM': 2,
            'SELF': 1,
        }
        
        max_priority = 0
        broadest_scope = 'SELF'
        custom_orgs = []
        
        for role in roles:
            priority = priority_map.get(role.data_scope, 0)
            if priority > max_priority:
                max_priority = priority
                broadest_scope = role.data_scope
                if role.data_scope == 'CUSTOM':
                    custom_orgs = list(role.custom_data_organizations.all())
        
        # 如果最宽泛的是CUSTOM，需要合并所有角色的自定义组织
        if broadest_scope == 'CUSTOM':
            custom_org_ids = set()
            for role in roles:
                if role.data_scope == 'CUSTOM':
                    custom_org_ids.update(role.custom_data_organizations.values_list('id', flat=True))
            # 获取所有自定义组织
            custom_orgs = list(Organization.objects.filter(id__in=custom_org_ids))
        
        return broadest_scope, custom_orgs

    def _filter_by_self(self, queryset: QuerySet, user) -> QuerySet:
        """过滤：仅本人数据（created_by=user）。"""
        if not self._model_has_field(queryset.model, 'created_by'):
            # 如果模型没有 created_by 字段，返回空查询集
            return queryset.none()
        return queryset.filter(created_by=user)

    def _filter_by_dept(self, queryset: QuerySet, user) -> QuerySet:
        """过滤：本部门数据（owner_organization=用户主组织）。"""
        if not self._model_has_field(queryset.model, 'owner_organization'):
            # 如果模型没有 owner_organization 字段，降级为仅本人数据
            return self._filter_by_self(queryset, user)
        
        # 获取用户的主组织
        primary_org = self._get_user_primary_org(user)
        if not primary_org:
            # 没有主组织，降级为仅本人数据
            return self._filter_by_self(queryset, user)
        
        return queryset.filter(owner_organization=primary_org)

    def _filter_by_dept_and_sub(self, queryset: QuerySet, user) -> QuerySet:
        """过滤：本部门及下级数据。"""
        if not self._model_has_field(queryset.model, 'owner_organization'):
            # 如果模型没有 owner_organization 字段，降级为仅本人数据
            return self._filter_by_self(queryset, user)
        
        # 获取用户的主组织
        primary_org = self._get_user_primary_org(user)
        if not primary_org:
            # 没有主组织，降级为仅本人数据
            return self._filter_by_self(queryset, user)
        
        # 获取主组织及其所有子组织的ID
        org_ids = self._get_org_and_children_ids(primary_org)
        
        return queryset.filter(owner_organization_id__in=org_ids)

    def _filter_by_custom(self, queryset: QuerySet, custom_orgs: List[Organization]) -> QuerySet:
        """过滤：自定义组织数据。"""
        if not self._model_has_field(queryset.model, 'owner_organization'):
            # 如果模型没有 owner_organization 字段，返回空查询集
            return queryset.none()
        
        if not custom_orgs:
            # 没有自定义组织，返回空查询集
            return queryset.none()
        
        org_ids = [org.id for org in custom_orgs]
        return queryset.filter(owner_organization_id__in=org_ids)

    def _model_has_field(self, model: type[models.Model], field_name: str) -> bool:
        """检查模型是否有指定字段。"""
        try:
            model._meta.get_field(field_name)
            return True
        except models.FieldDoesNotExist:
            return False

    def _get_user_primary_org(self, user) -> Optional[Organization]:
        """获取用户的主组织。"""
        try:
            uo = UserOrganization.objects.filter(user=user, is_primary=True).select_related('organization').first()
            if uo:
                return uo.organization
        except Exception:
            pass
        return None

    def _get_org_and_children_ids(self, org: Organization) -> List[int]:
        """获取组织及其所有子组织的ID列表（递归）。"""
        org_ids = [org.id]
        
        def get_children(organization):
            """递归获取子组织。"""
            children = Organization.objects.filter(parent=organization)
            for child in children:
                org_ids.append(child.id)
                get_children(child)  # 递归获取子组织的子组织
        
        get_children(org)
        return org_ids

