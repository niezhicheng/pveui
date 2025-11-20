"""知识库视图集。"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.data_mixins import DataScopeFilterMixin
from apps.common.mixins import AuditOwnerPopulateMixin, SoftDeleteMixin
from apps.common.viewsets import ActionSerializerMixin

from .models import KnowledgeArticle
from .serializers import (
    KnowledgeArticleListSerializer,
    KnowledgeArticleDetailSerializer,
    KnowledgeArticleCreateSerializer,
    KnowledgeArticleUpdateSerializer,
)


class KnowledgeArticleViewSet(
    DataScopeFilterMixin,
    AuditOwnerPopulateMixin,
    SoftDeleteMixin,
    ActionSerializerMixin,
    viewsets.ModelViewSet,
):
    """知识库文章 CRUD。"""

    queryset = (
        KnowledgeArticle.objects.select_related(
            'owner_organization',
            'created_by',
            'updated_by',
        )
        .all()
        .order_by('-is_pinned', '-updated_at', '-id')
    )
    permission_classes = [permissions.IsAuthenticated]

    serializer_class = KnowledgeArticleDetailSerializer
    list_serializer_class = KnowledgeArticleListSerializer
    retrieve_serializer_class = KnowledgeArticleDetailSerializer
    create_serializer_class = KnowledgeArticleCreateSerializer
    update_serializer_class = KnowledgeArticleUpdateSerializer
    partial_update_serializer_class = KnowledgeArticleUpdateSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_published', 'is_pinned', 'owner_organization']
    search_fields = ['title', 'summary', 'content', 'tags']
    ordering_fields = ['id', 'title', 'created_at', 'updated_at', 'is_pinned']

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """返回可选分类。"""
        return Response(
            [
                {'value': key, 'label': label}
                for key, label in KnowledgeArticle.CATEGORY_CHOICES
            ]
        )


