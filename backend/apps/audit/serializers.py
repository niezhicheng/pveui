"""操作日志序列化器。"""

from rest_framework import serializers
from .models import OperationLog


class OperationLogSerializer(serializers.ModelSerializer):
    """操作日志序列化器。"""

    # 扩展字段
    user_display = serializers.CharField(source='user.username', read_only=True, default='')
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    content_type_display = serializers.CharField(source='content_type.model', read_only=True, default='')

    class Meta:
        model = OperationLog
        fields = [
            'id',
            'user',
            'user_display',
            'username',
            'created_at',
            'action_type',
            'action_type_display',
            'content_type',
            'content_type_display',
            'object_id',
            'object_repr',
            'request_path',
            'request_method',
            'request_params',
            'ip_address',
            'user_agent',
            'status_code',
            'error_message',
            'remark',
        ]
        read_only_fields = fields

