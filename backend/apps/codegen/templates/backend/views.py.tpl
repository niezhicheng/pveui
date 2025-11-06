from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from apps.${AppLabel}.models import ${ModelName}
from .serializers import ${ModelName}Serializer


class ${ModelName}ViewSet(viewsets.ModelViewSet):
    """基础 CRUD 视图集

    - 使用 DRF 内置过滤/搜索/排序
    - 后续可接入 RBAC/DataScope/审计等增强能力
    """

    queryset = ${ModelName}.objects.all().order_by('-id')
    serializer_class = ${ModelName}Serializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['id']
    ordering_fields = ['id']

