"""操作日志 URL 配置。"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OperationLogViewSet

router = DefaultRouter()
router.register(r'logs', OperationLogViewSet, basename='operation-log')

urlpatterns = [
    path('', include(router.urls)),
]

