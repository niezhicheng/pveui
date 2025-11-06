"""操作日志视图集。"""

from rest_framework import viewsets, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from apps.common.pagination import LargePageSizePagination
from .models import OperationLog
from .serializers import OperationLogSerializer


class OperationLogFilter(django_filters.FilterSet):
    """操作日志过滤器。"""

    # 时间范围过滤
    created_at_start = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_end = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    # 操作类型过滤
    action_type = django_filters.ChoiceFilter(choices=OperationLog.ACTION_CHOICES)

    class Meta:
        model = OperationLog
        fields = ['user', 'action_type', 'request_method', 'status_code', 'ip_address']


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """操作日志视图集：只读（不允许创建/更新/删除）。"""

    queryset = OperationLog.objects.select_related('user', 'content_type').all().order_by('-created_at')
    serializer_class = OperationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LargePageSizePagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OperationLogFilter
    search_fields = ['username', 'request_path', 'object_repr', 'ip_address', 'error_message']
    ordering_fields = ['created_at', 'id']

