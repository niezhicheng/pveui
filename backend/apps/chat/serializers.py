"""聊天模块序列化器。"""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import ChatMessage

User = get_user_model()


class ChatMessageSerializer(serializers.ModelSerializer):
    """聊天消息序列化器。"""
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    receiver_id = serializers.IntegerField(source='receiver.id', read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'sender', 'sender_id', 'sender_username',
            'receiver', 'receiver_id', 'receiver_username',
            'content', 'is_read', 'read_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['sender', 'created_at', 'updated_at', 'is_read', 'read_at']


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    """创建聊天消息序列化器。"""
    
    class Meta:
        model = ChatMessage
        fields = ['receiver', 'content']


class UserChatSummarySerializer(serializers.Serializer):
    """用户聊天摘要序列化器（用于显示聊天列表）。"""
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    last_message = serializers.CharField(allow_null=True)
    last_message_time = serializers.DateTimeField(allow_null=True)
    unread_count = serializers.IntegerField()

