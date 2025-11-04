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
"""项目 URL 路由入口。

包含：
- Django Admin
- RBAC 接口路由（apps.rbac.urls）
- 媒体文件（仅在配置了 MEDIA_ROOT 时）
"""

from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.views.static import serve
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/rbac/', include('apps.rbac.urls')),
    path('api/curd/', include('apps.curdexample.urls')),
    path('api/common/', include('apps.common.urls')),
    path('api/codegen/', include('apps.codegen.urls')),
    path('api/book/', include('apps.book.urls')),
]

# 仅当定义了 MEDIA_ROOT 时才添加媒体文件映射（避免导入期 AttributeError）
if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
