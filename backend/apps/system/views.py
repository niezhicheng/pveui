"""系统设置视图集。"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction

from apps.common.viewsets import ActionSerializerMixin
from apps.common.mixins import AuditOwnerPopulateMixin
from .models import SystemSetting
from .serializers import (
    SystemSettingListSerializer,
    SystemSettingDetailSerializer,
    SystemSettingCreateSerializer,
    SystemSettingUpdateSerializer,
    SystemSettingBulkUpdateSerializer,
)


class SystemSettingViewSet(AuditOwnerPopulateMixin, ActionSerializerMixin, viewsets.ModelViewSet):
    """系统设置 CRUD 视图集。"""
    
    queryset = SystemSetting.objects.all().order_by('category', 'key')
    
    # 兜底序列化器
    serializer_class = SystemSettingDetailSerializer
    
    # 按动作切换序列化器
    list_serializer_class = SystemSettingListSerializer
    retrieve_serializer_class = SystemSettingDetailSerializer
    create_serializer_class = SystemSettingCreateSerializer
    update_serializer_class = SystemSettingUpdateSerializer
    partial_update_serializer_class = SystemSettingUpdateSerializer
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_encrypted', 'is_public']
    search_fields = ['key', 'description']
    ordering_fields = ['id', 'key', 'category', 'created_at']
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """按分类获取设置。"""
        category = request.query_params.get('category', '')
        if category:
            settings = self.queryset.filter(category=category)
        else:
            settings = self.queryset.all()
        
        # 按分类分组
        result = {}
        for setting in settings:
            if setting.category not in result:
                result[setting.category] = []
            serializer = SystemSettingListSerializer(setting)
            result[setting.category].append(serializer.data)
        
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """批量更新设置。"""
        serializer = SystemSettingBulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        settings_data = serializer.validated_data['settings']
        updated_count = 0
        errors = []
        
        with transaction.atomic():
            for item in settings_data:
                try:
                    setting = SystemSetting.objects.get(key=item['key'])
                    setting.value = item['value']
                    if 'description' in item:
                        setting.description = item['description']
                    if 'category' in item:
                        setting.category = item['category']
                    setting.save()
                    updated_count += 1
                except SystemSetting.DoesNotExist:
                    errors.append(f"设置 '{item['key']}' 不存在")
                except Exception as e:
                    errors.append(f"更新设置 '{item['key']}' 失败: {str(e)}")
        
        if errors:
            return Response({
                'detail': f'部分更新失败',
                'updated_count': updated_count,
                'errors': errors
            }, status=status.HTTP_207_MULTI_STATUS)
        
        return Response({
            'detail': f'成功更新 {updated_count} 个设置',
            'updated_count': updated_count
        })
    
    @action(detail=False, methods=['get'])
    def get_by_key(self, request):
        """根据 key 获取单个设置值。"""
        key = request.query_params.get('key')
        if not key:
            return Response({'detail': '缺少 key 参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            setting = SystemSetting.objects.get(key=key)
            return Response({
                'key': setting.key,
                'value': setting.value,
                'description': setting.description,
                'category': setting.category
            })
        except SystemSetting.DoesNotExist:
            return Response({'detail': f'设置 {key} 不存在'}, status=status.HTTP_404_NOT_FOUND)

