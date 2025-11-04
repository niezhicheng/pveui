from rest_framework import permissions, filters, viewsets
from django_filters.rest_framework import DjangoFilterBackend

from apps.common.viewsets import ActionSerializerMixin
from apps.common.mixins import AuditOwnerPopulateMixin, SoftDeleteMixin
from apps.common.data_mixins import DataScopeFilterMixin
from .models import Example
from .serializers import (
    ExampleListSerializer,
    ExampleDetailSerializer,
    ExampleCreateSerializer,
    ExampleUpdateSerializer,
)


class ExampleViewSet(DataScopeFilterMixin, AuditOwnerPopulateMixin, SoftDeleteMixin, ActionSerializerMixin, viewsets.ModelViewSet):
    """示例 CRUD 视图集：支持按动作切换序列化器。"""
    queryset = Example.objects.select_related(
        'owner_organization',
        'created_by',
        'updated_by'
    ).all().order_by('-id')
    permission_classes = [permissions.IsAuthenticated]

    # 兜底
    serializer_class = ExampleDetailSerializer

    # 按动作切换
    list_serializer_class = ExampleListSerializer
    retrieve_serializer_class = ExampleDetailSerializer
    create_serializer_class = ExampleCreateSerializer
    update_serializer_class = ExampleUpdateSerializer
    partial_update_serializer_class = ExampleUpdateSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'owner_organization']
    search_fields = ['name', 'description']
    ordering_fields = ['id', 'name', 'price', 'created_at']

