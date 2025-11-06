"""
URL configuration for django_vue_adminx project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""RBAC 路由注册。

使用 DRF DefaultRouter 自动生成标准 CRUD 路由：
 /api/rbac/<resource>/ 和 /api/rbac/<resource>/{pk}/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MenuViewSet,
    PermissionViewSet,
    RoleViewSet,
    UserViewSet,
    UserRoleViewSet,
    OrganizationViewSet,
    UserOrganizationViewSet,
    LoginView,
    LogoutView,
    UserInfoView,
    CheckPermissionView,
    ChangePasswordView,
    UserPermissionsView,
    UserOrganizationsView,
    OrganizationTreeView,
    MenuTreeView,
    SystemMetricsView,
    DashboardView,
)

# 可根据需要将 basename 显式指定，当前使用默认模型名推导
router = DefaultRouter()
router.register(r'menus', MenuViewSet)
router.register(r'permissions', PermissionViewSet)
router.register(r'roles', RoleViewSet)
router.register(r'users', UserViewSet)
router.register(r'user-roles', UserRoleViewSet)
router.register(r'organizations', OrganizationViewSet)
router.register(r'user-organizations', UserOrganizationViewSet)

urlpatterns = [
    # 将特殊路由放在 router.urls 之前，避免路由冲突
    path('organizations/tree/', OrganizationTreeView.as_view()),
    path('menu-tree/', MenuTreeView.as_view()),
    path('system/metrics/', SystemMetricsView.as_view()),
    path('dashboard/', DashboardView.as_view()),
    path('auth/login/', LoginView.as_view()),
    path('auth/logout/', LogoutView.as_view()),
    path('auth/user-info/', UserInfoView.as_view()),
    path('auth/check-permission/', CheckPermissionView.as_view()),
    path('auth/change-password/', ChangePasswordView.as_view()),
    path('auth/permissions/', UserPermissionsView.as_view()),
    path('auth/organizations/', UserOrganizationsView.as_view()),
    # router 的路由放在最后
    path('', include(router.urls)),
]
