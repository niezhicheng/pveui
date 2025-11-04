"""RBAC 权限控制类。

提供基于 Permission 模型的 API 权限拦截。
"""

import re
from django.db.models import Q
from rest_framework import permissions
from .models import Permission, Role


class RBACPermission(permissions.BasePermission):
    """基于 RBAC 模型的权限控制。
    
    根据请求的 URL 和 HTTP 方法，查找对应的 Permission 记录，
    检查当前用户是否通过角色拥有该权限。
    
    超级用户自动拥有所有权限。
    """

    def has_permission(self, request, view):
        """检查用户是否有权限访问该视图。
        
        Args:
            request: DRF 请求对象
            view: DRF 视图对象
            
        Returns:
            bool: 如果用户有权限返回 True，否则返回 False
        """
        # 未认证用户拒绝访问
        if not request.user or not request.user.is_authenticated:
            return False

        # 超级用户拥有所有权限
        if request.user.is_superuser:
            return True

        # 获取请求的 URL 路径和 HTTP 方法
        url_path = request.path
        http_method = request.method.upper()

        # 查找匹配的权限记录
        # 1. 精确匹配 URL 和方法
        # 2. URL 使用正则匹配（支持通配符）
        matched_perms = Permission.objects.filter(
            is_active=True
        ).filter(
            # 方法匹配：ANY 或具体方法
            Q(http_method='ANY') | Q(http_method=http_method)
        )

        # 检查是否有权限匹配当前 URL
        matched_permission = None
        for perm in matched_perms:
            # 将 URL pattern 转换为正则表达式
            pattern = self._url_pattern_to_regex(perm.url_pattern)
            if re.match(pattern, url_path):
                matched_permission = perm
                break

        # 如果没有找到匹配的权限记录，默认允许（向后兼容）
        # 这样可以避免需要为所有接口都配置权限
        if not matched_permission:
            return True

        # 找到了匹配的权限记录，检查用户是否拥有该权限
        if self._user_has_permission(request.user, matched_permission):
            return True

        # 用户没有权限
        return False

    def _url_pattern_to_regex(self, pattern):
        """将 URL pattern 转换为正则表达式。
        
        Args:
            pattern: URL 模式字符串，支持通配符 * 和参数 {id}
            
        Returns:
            str: 正则表达式字符串
        """
        # 如果 pattern 以 / 结尾，移除末尾的 /
        if pattern.endswith('/'):
            pattern = pattern.rstrip('/')
        
        # 转义特殊字符（但保留 * 和 {}）
        # 先处理通配符和参数占位符
        pattern = pattern.replace('*', '__WILDCARD__')
        pattern = pattern.replace('{', '__PARAM_START__')
        pattern = pattern.replace('}', '__PARAM_END__')
        
        # 转义其他特殊字符
        pattern = re.escape(pattern)
        
        # 恢复通配符和参数占位符，并转换为正则表达式
        pattern = pattern.replace('__WILDCARD__', '.*')
        pattern = pattern.replace('__PARAM_START__', r'\{')
        pattern = pattern.replace('__PARAM_END__', r'\}')
        
        # 将 {id} 形式的参数转换为数字匹配（支持多个参数）
        pattern = re.sub(r'\\\{[^}]+\\\}', r'\\d+', pattern)
        
        # 确保匹配完整路径（支持以 / 结尾或带参数）
        if not pattern.endswith('.*'):
            pattern = pattern + '(?:/.*)?$'
        else:
            pattern = pattern + '$'
        
        return pattern

    def _user_has_permission(self, user, permission):
        """检查用户是否拥有指定权限。
        
        Args:
            user: 用户对象
            permission: Permission 对象
            
        Returns:
            bool: 如果用户拥有权限返回 True
        """
        # 获取用户的所有角色
        user_roles = Role.objects.filter(user_roles__user=user).distinct()
        
        # 检查权限是否属于这些角色
        return permission.roles.filter(id__in=user_roles.values_list('id', flat=True)).exists()


# 为了更精确的匹配，也可以使用基于权限编码的方式
class RBACPermissionByCode(permissions.BasePermission):
    """基于权限编码的权限控制。
    
    需要在 ViewSet 中定义 permission_code_map 属性，映射 action 到权限编码。
    例如：
        permission_code_map = {
            'list': 'user:list',
            'create': 'user:create',
            'update': 'user:update',
            'destroy': 'user:delete',
        }
    """

    def has_permission(self, request, view):
        """检查用户是否有权限访问该视图。"""
        # 未认证用户拒绝访问
        if not request.user or not request.user.is_authenticated:
            return False

        # 超级用户拥有所有权限
        if request.user.is_superuser:
            return True

        # 获取当前 action 对应的权限编码
        action = getattr(view, 'action', None)
        if not action:
            # 对于非 ViewSet 的视图，尝试从 request 中获取
            action = self._get_action_from_request(request, view)

        # 获取权限编码映射
        permission_code_map = getattr(view, 'permission_code_map', {})

        # 如果没有配置权限编码，默认允许（向后兼容）
        if not permission_code_map or action not in permission_code_map:
            return True

        permission_code = permission_code_map[action]

        # 检查用户是否拥有该权限
        user_roles = Role.objects.filter(user_roles__user=request.user).distinct()
        has_perm = Permission.objects.filter(
            code=permission_code,
            roles__in=user_roles,
            is_active=True
        ).exists()

        return has_perm

    def _get_action_from_request(self, request, view):
        """从请求中推断 action。"""
        method = request.method.upper()
        action_map = {
            'GET': 'list' if not hasattr(view, 'lookup_url_kwarg') else 'retrieve',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'partial_update',
            'DELETE': 'destroy',
        }
        return action_map.get(method, 'list')

