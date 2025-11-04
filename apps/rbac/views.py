"""RBAC 视图集。

提供各模型的标准 CRUD；支持过滤、搜索与排序。
默认权限使用 IsAuthenticated，如需匿名访问可在 settings 中调整 DRF 默认权限。
"""

from typing import Dict, List

from django.contrib.auth import authenticate, login, logout
from rest_framework import viewsets, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Menu, Permission, Role, UserRole, Organization, UserOrganization
from .serializers import (
    MenuSerializer,
    PermissionSerializer,
    RoleSerializer,
    UserRoleSerializer,
    OrganizationSerializer,
    UserOrganizationSerializer,
)


class DefaultPermission(permissions.IsAuthenticated):
    """默认认证权限：要求登录。"""
    pass


class MenuViewSet(viewsets.ModelViewSet):
    """菜单 CRUD 与列表检索。"""
    queryset = Menu.objects.all().order_by('order', 'id')
    serializer_class = MenuSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent', 'is_hidden']
    search_fields = ['title', 'path', 'component']
    ordering_fields = ['order', 'id', 'title']


class PermissionViewSet(viewsets.ModelViewSet):
    """权限 CRUD 与列表检索。"""
    queryset = Permission.objects.all().order_by('id')
    serializer_class = PermissionSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['http_method', 'menu', 'is_active']
    search_fields = ['name', 'code', 'url_pattern']
    ordering_fields = ['id', 'code', 'name']


class RoleViewSet(viewsets.ModelViewSet):
    """角色 CRUD 与列表检索，支持 data_scope 与自定义组织集合。"""
    queryset = Role.objects.all().order_by('id')
    serializer_class = RoleSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['data_scope']
    search_fields = ['name', 'code']
    ordering_fields = ['id', 'name', 'code']


class UserRoleViewSet(viewsets.ModelViewSet):
    """用户-角色绑定 CRUD 与列表检索。"""
    queryset = UserRole.objects.all().order_by('-created_at')
    serializer_class = UserRoleSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'role']
    search_fields = ['user__username', 'role__name']
    ordering_fields = ['created_at', 'id']


class OrganizationViewSet(viewsets.ModelViewSet):
    """组织 CRUD 与列表检索。"""
    queryset = Organization.objects.all().order_by('order', 'id')
    serializer_class = OrganizationSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'code']
    ordering_fields = ['order', 'id', 'name']


class UserOrganizationViewSet(viewsets.ModelViewSet):
    """用户-组织绑定 CRUD 与列表检索。"""
    queryset = UserOrganization.objects.all().order_by('-created_at')
    serializer_class = UserOrganizationSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'organization', 'is_primary']
    search_fields = ['user__username', 'organization__name']
    ordering_fields = ['created_at', 'id']


class LoginView(APIView):
    """登录接口：Django Session 认证。"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):  # noqa: D401
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({"detail": "用户名或密码不能为空"}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"detail": "用户名或密码错误"}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({"detail": "用户未启用"}, status=status.HTTP_403_FORBIDDEN)

        login(request, user)

        role_qs = Role.objects.filter(user_roles__user=user).distinct()
        perm_qs = Permission.objects.filter(roles__in=role_qs, is_active=True).distinct()
        data = {
            "id": user.id,
            "username": getattr(user, 'username', ''),
            "roles": list(role_qs.values_list('code', flat=True)),
            "permissions": list(perm_qs.values_list('code', flat=True)),
        }
        return Response(data)


class LogoutView(APIView):
    """退出登录接口：清除 Session。"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):  # noqa: D401
        logout(request)
        return Response({"detail": "退出成功"})


class UserInfoView(APIView):
    """获取当前用户信息：基本信息、角色、权限、主组织。"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):  # noqa: D401
        user = request.user
        role_qs = Role.objects.filter(user_roles__user=user).distinct()
        perm_qs = Permission.objects.filter(roles__in=role_qs, is_active=True).distinct()

        # 获取主组织
        primary_org = None
        try:
            from .models import UserOrganization
            uo = UserOrganization.objects.filter(user=user, is_primary=True).select_related('organization').first()
            if uo:
                primary_org = {
                    "id": uo.organization.id,
                    "name": uo.organization.name,
                    "code": uo.organization.code,
                }
        except Exception:
            pass

        data = {
            "id": user.id,
            "username": getattr(user, 'username', ''),
            "email": getattr(user, 'email', ''),
            "is_superuser": user.is_superuser,
            "roles": list(role_qs.values('id', 'name', 'code')),
            "permissions": list(perm_qs.values_list('code', flat=True)),
            "primary_organization": primary_org,
        }
        return Response(data)


class CheckPermissionView(APIView):
    """权限检查接口：用于前端按钮级权限控制。

    Request JSON: { "code": "permission_code" }
    Response JSON: { "has_permission": true/false }
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):  # noqa: D401
        code = request.data.get('code')
        if not code:
            return Response({"detail": "权限编码不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if user.is_superuser:
            return Response({"has_permission": True})

        role_qs = Role.objects.filter(user_roles__user=user).distinct()
        has_perm = Permission.objects.filter(
            code=code,
            roles__in=role_qs,
            is_active=True
        ).exists()

        return Response({"has_permission": has_perm})


class ChangePasswordView(APIView):
    """修改密码接口。

    Request JSON: { "old_password": "...", "new_password": "..." }
    Response JSON: { "detail": "修改成功" }
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):  # noqa: D401
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response({"detail": "旧密码和新密码不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 6:
            return Response({"detail": "新密码长度至少6位"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(old_password):
            return Response({"detail": "旧密码错误"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"detail": "密码修改成功"})


class UserPermissionsView(APIView):
    """获取当前用户所有权限列表（包含权限详情）。"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):  # noqa: D401
        user = request.user
        if user.is_superuser:
            permissions_list = list(
                Permission.objects.filter(is_active=True).values('id', 'name', 'code', 'http_method', 'url_pattern')
            )
        else:
            role_qs = Role.objects.filter(user_roles__user=user).distinct()
            permissions_list = list(
                Permission.objects.filter(roles__in=role_qs, is_active=True).distinct()
                .values('id', 'name', 'code', 'http_method', 'url_pattern')
            )

        return Response({"permissions": permissions_list})


class UserOrganizationsView(APIView):
    """获取当前用户所属组织信息（包含主组织标记）。"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):  # noqa: D401
        user = request.user
        uo_list = UserOrganization.objects.filter(user=user).select_related('organization').order_by('-is_primary', 'created_at')

        organizations = []
        primary_org = None
        for uo in uo_list:
            org_data = {
                "id": uo.organization.id,
                "name": uo.organization.name,
                "code": uo.organization.code,
                "is_primary": uo.is_primary,
                "created_at": uo.created_at.isoformat() if uo.created_at else None,
            }
            organizations.append(org_data)
            if uo.is_primary:
                primary_org = org_data

        return Response({
            "organizations": organizations,
            "primary_organization": primary_org,
        })


class OrganizationTreeView(APIView):
    """获取组织树（用于前端组织选择器）。

    可选参数：only_active (bool) - 仅返回启用组织
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):  # noqa: D401
        only_active = request.query_params.get('only_active', 'false').lower() == 'true'
        qs = Organization.objects.all()
        if only_active:
            qs = qs.filter(is_active=True)
        orgs = list(qs.order_by('order', 'id'))

        def to_node(o: Organization) -> Dict:
            return {
                "id": o.id,
                "name": o.name,
                "code": o.code,
                "order": o.order,
                "is_active": o.is_active,
                "parent": o.parent_id,
                "leader_id": o.leader_id if o.leader else None,
                "children": [],
            }

        node_map: Dict[int, Dict] = {o.id: to_node(o) for o in orgs}
        roots: List[Dict] = []
        for o in orgs:
            node = node_map[o.id]
            if o.parent_id and o.parent_id in node_map:
                node_map[o.parent_id]["children"].append(node)
            else:
                roots.append(node)

        def sort_tree(nodes: List[Dict]):
            nodes.sort(key=lambda n: (n.get('order', 0), n.get('id', 0)))
            for n in nodes:
                sort_tree(n.get('children', []))

        sort_tree(roots)
        return Response(roots)


class MenuTreeView(APIView):
    """返回当前用户可见的菜单树。"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):  # noqa: D401
        user = request.user
        if user.is_superuser:
            menus = list(Menu.objects.filter(is_hidden=False).order_by('order', 'id'))
        else:
            role_qs = Role.objects.filter(user_roles__user=user).distinct()
            menus = list(
                Menu.objects.filter(roles__in=role_qs, is_hidden=False).distinct().order_by('order', 'id')
            )

        def to_node(m: Menu) -> Dict:
            return {
                "id": m.id,
                "title": m.title,
                "path": m.path,
                "component": m.component,
                "icon": m.icon,
                "order": m.order,
                "parent": m.parent_id,
                "children": [],
            }

        node_map: Dict[int, Dict] = {m.id: to_node(m) for m in menus}
        roots: List[Dict] = []
        for m in menus:
            node = node_map[m.id]
            if m.parent_id and m.parent_id in node_map:
                node_map[m.parent_id]["children"].append(node)
            else:
                roots.append(node)

        def sort_tree(nodes: List[Dict]):
            nodes.sort(key=lambda n: (n.get('order', 0), n.get('id', 0)))
            for n in nodes:
                sort_tree(n.get('children', []))

        sort_tree(roots)
        return Response(roots)

