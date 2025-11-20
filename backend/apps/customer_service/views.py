"""客服系统视图。"""

from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.common.mixins import AuditOwnerPopulateMixin
from apps.common.viewsets import ActionSerializerMixin
from .models import GuestSession, GuestMessage
from .serializers import (
    GuestSessionSerializer,
    GuestSessionListSerializer,
    GuestMessageSerializer,
    GuestMessageCreateSerializer,
    GuestSessionInitSerializer,
    GuestMessagePublicSerializer,
    AgentMessageSendSerializer,
)


def notify_session_message(session, message):
    """向会话推送实时消息。"""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    data = GuestMessageSerializer(message).data
    async_to_sync(channel_layer.group_send)(
        f"cs_session_{session.session_id}",
        {
            "type": "session_message",
            "message": data,
        }
    )


class GuestSessionViewSet(AuditOwnerPopulateMixin, ActionSerializerMixin, viewsets.ModelViewSet):
    """后台客服查看访客会话。"""

    queryset = GuestSession.objects.select_related('assigned_to').all()
    permission_classes = [permissions.IsAuthenticated]

    serializer_class = GuestSessionSerializer
    list_serializer_class = GuestSessionListSerializer
    retrieve_serializer_class = GuestSessionSerializer
    update_serializer_class = GuestSessionSerializer
    partial_update_serializer_class = GuestSessionSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'app_id', 'assigned_to']
    search_fields = ['session_id', 'nickname', 'visitor_id', 'contact']
    ordering_fields = ['last_message_at', 'created_at']
    ordering = ['-last_message_at', '-created_at']

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """分配客服。"""
        session = self.get_object()
        session.assigned_to = request.user
        session.status = 'active'
        session.save(update_fields=['assigned_to', 'status'])
        return Response({'detail': '已分配给当前用户'})

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        session = self.get_object()
        session.status = 'closed'
        session.save(update_fields=['status'])
        return Response({'detail': '会话已关闭'})

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """客服发送消息。"""
        session = self.get_object()
        serializer = AgentMessageSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        message = GuestMessage.objects.create(
            session=session,
            sender_type='agent',
            sender=request.user,
            content=data['content'],
            message_type=data['message_type'],
        )

        session.last_message = data['content']
        session.last_message_at = timezone.now()
        session.status = 'active'
        session.save(update_fields=['last_message', 'last_message_at', 'status'])

        notify_session_message(session, message)

        return Response(GuestMessageSerializer(message).data, status=status.HTTP_201_CREATED)


class GuestMessageViewSet(AuditOwnerPopulateMixin, viewsets.ReadOnlyModelViewSet):
    """后台客服查看会话消息。"""

    serializer_class = GuestMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        session_id = self.request.query_params.get('session_id')
        queryset = GuestMessage.objects.select_related('session', 'sender')
        if session_id:
            queryset = queryset.filter(session__session_id=session_id)
        return queryset.order_by('created_at')


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def guest_session_init(request):
    """访客初始化会话，返回 session_id 和 secret_token。"""
    serializer = GuestSessionInitSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    session = GuestSession.objects.create(
        app_id=data['app_id'],
        visitor_id=data.get('visitor_id', ''),
        nickname=data.get('nickname', '访客'),
        contact=data.get('contact', ''),
        source_url=data.get('source_url', ''),
        metadata=data.get('metadata', {}),
        status='pending',
    )
    return Response({
        'session_id': session.session_id,
        'secret_token': session.secret_token,
        'nickname': session.nickname,
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def guest_message_send(request):
    """访客发送消息。"""
    serializer = GuestMessagePublicSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    session = get_object_or_404(
        GuestSession,
        session_id=data['session_id'],
        secret_token=data['secret_token'],
    )

    message = GuestMessage.objects.create(
        session=session,
        sender_type='guest',
        content=data['content'],
        message_type=data['message_type'],
    )

    session.last_message = data['content']
    session.last_message_at = timezone.now()
    session.status = 'active'
    session.save(update_fields=['last_message', 'last_message_at', 'status'])

    notify_session_message(session, message)

    return Response(GuestMessageSerializer(message).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def guest_message_history(request):
    """访客查询历史消息。"""
    session_id = request.query_params.get('session_id')
    secret_token = request.query_params.get('secret_token')
    if not session_id or not secret_token:
        return Response({'detail': '缺少参数'}, status=status.HTTP_400_BAD_REQUEST)

    session = get_object_or_404(
        GuestSession,
        session_id=session_id,
        secret_token=secret_token,
    )
    messages = session.messages.order_by('created_at')
    data = GuestMessageSerializer(messages, many=True).data
    return Response(data)


