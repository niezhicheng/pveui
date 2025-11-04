

from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from apps.common.viewsets import ActionSerializerMixin
from apps.common.mixins import AuditOwnerPopulateMixin, SoftDeleteMixin
from apps.common.data_mixins import DataScopeFilterMixin
from apps.book.models import Book
from .serializers import (
    BookListSerializer,
    BookDetailSerializer,
    BookCreateSerializer,
    BookUpdateSerializer,
)


class BookViewSet(DataScopeFilterMixin, AuditOwnerPopulateMixin, SoftDeleteMixin, ActionSerializerMixin, viewsets.ModelViewSet):
    """增强型 CRUD 视图集（与 curdexample 一致）

    - DataScopeFilterMixin：按角色数据权限自动过滤数据范围
    - AuditOwnerPopulateMixin：创建/更新时自动填充 created_by/updated_by/owner_organization
    - SoftDeleteMixin：软删除支持
    - ActionSerializerMixin：按动作切换序列化器（列表/详情/创建/更新）
    """

    queryset = Book.objects.select_related('owner_organization', 'created_by', 'updated_by').all().order_by('-id')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['owner_organization', 'is_deleted']
    search_fields = ['id']
    ordering_fields = ['id', 'created_at']

    # 默认
    serializer_class = BookDetailSerializer

    # 按动作切换
    list_serializer_class = BookListSerializer
    retrieve_serializer_class = BookDetailSerializer
    create_serializer_class = BookCreateSerializer
    update_serializer_class = BookUpdateSerializer
    partial_update_serializer_class = BookUpdateSerializer


