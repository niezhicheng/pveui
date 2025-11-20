"""系统设置序列化器。"""

from rest_framework import serializers
from apps.common.serializers import BaseModelSerializer
from .models import SystemSetting


class SystemSettingListSerializer(BaseModelSerializer):
    """系统设置列表序列化器：用于列表展示。"""
    
    class Meta:
        model = SystemSetting
        fields = [
            'id', 'key', 'value', 'description', 'category', 
            'is_encrypted', 'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SystemSettingDetailSerializer(BaseModelSerializer):
    """系统设置详情序列化器：用于详情展示。"""
    
    class Meta:
        model = SystemSetting
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class SystemSettingCreateSerializer(BaseModelSerializer):
    """系统设置创建序列化器：用于创建操作。"""
    
    class Meta:
        model = SystemSetting
        fields = ['key', 'value', 'description', 'category', 'is_encrypted', 'is_public', 'remark']


class SystemSettingUpdateSerializer(BaseModelSerializer):
    """系统设置更新序列化器：用于更新操作。"""
    
    class Meta:
        model = SystemSetting
        fields = ['value', 'description', 'category', 'is_encrypted', 'is_public', 'remark']


class SystemSettingBulkUpdateSerializer(serializers.Serializer):
    """批量更新系统设置序列化器。"""
    
    settings = serializers.ListField(
        child=serializers.DictField(),
        help_text='设置列表，每个设置包含 key 和 value'
    )
    
    def validate_settings(self, value):
        """验证设置列表。"""
        if not value:
            raise serializers.ValidationError("设置列表不能为空")
        
        for item in value:
            if 'key' not in item:
                raise serializers.ValidationError("每个设置必须包含 'key' 字段")
            if 'value' not in item:
                raise serializers.ValidationError("每个设置必须包含 'value' 字段")
        
        return value

