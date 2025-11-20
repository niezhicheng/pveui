"""客服系统序列化器。"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.common.serializers import BaseModelSerializer
from .models import GuestSession, GuestMessage

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class GuestMessageSerializer(BaseModelSerializer):
    sender = SimpleUserSerializer(read_only=True)

    class Meta:
        model = GuestMessage
        fields = '__all__'
        read_only_fields = ['session', 'sender', 'sender_type', 'message_type', 'is_read']


class GuestMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestMessage
        fields = ['session', 'content', 'message_type']


class GuestSessionSerializer(BaseModelSerializer):
    assigned_to = SimpleUserSerializer(read_only=True)

    class Meta:
        model = GuestSession
        fields = '__all__'
        read_only_fields = [
            'session_id',
            'secret_token',
            'last_message',
            'last_message_at',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]


class GuestSessionListSerializer(BaseModelSerializer):
    assigned_to = SimpleUserSerializer(read_only=True)

    class Meta:
        model = GuestSession
        fields = [
            'id',
            'session_id',
            'app_id',
            'visitor_id',
            'nickname',
            'status',
            'assigned_to',
            'last_message',
            'last_message_at',
            'created_at',
        ]


class GuestSessionInitSerializer(serializers.Serializer):
    app_id = serializers.CharField(max_length=64)
    visitor_id = serializers.CharField(max_length=128, required=False, allow_blank=True)
    nickname = serializers.CharField(max_length=64, required=False, allow_blank=True)
    contact = serializers.CharField(max_length=128, required=False, allow_blank=True)
    source_url = serializers.URLField(required=False, allow_blank=True)
    metadata = serializers.DictField(required=False, default=dict)


class GuestMessagePublicSerializer(serializers.Serializer):
    session_id = serializers.CharField(max_length=64)
    secret_token = serializers.CharField(max_length=64)
    content = serializers.CharField()
    message_type = serializers.ChoiceField(choices=['text', 'image', 'file', 'event'], default='text')


class AgentMessageSendSerializer(serializers.Serializer):
    content = serializers.CharField()
    message_type = serializers.ChoiceField(choices=['text', 'image', 'file', 'event'], default='text')



