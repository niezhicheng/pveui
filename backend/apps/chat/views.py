"""聊天模块视图。"""

from django.contrib.auth import get_user_model
from django.db.models import Q, Max, Count, Case, When, IntegerField
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ChatMessage
from .serializers import (
    ChatMessageSerializer,
    ChatMessageCreateSerializer,
    UserChatSummarySerializer,
)

User = get_user_model()
channel_layer = get_channel_layer()


class ChatMessageViewSet(viewsets.ModelViewSet):
    """聊天消息视图集。"""
    permission_classes = [IsAuthenticated]
    queryset = ChatMessage.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return ChatMessageCreateSerializer
        return ChatMessageSerializer

    def get_queryset(self):
        """只返回当前用户相关的消息。"""
        user = self.request.user
        return ChatMessage.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('sender', 'receiver').order_by('-created_at')

    def perform_create(self, serializer):
        """创建消息时自动设置发送者，并通过WebSocket推送。"""
        message = serializer.save(sender=self.request.user)
        
        # 通过WebSocket推送消息给接收者
        self.send_message_via_websocket(message)
        
        # 同时通知发送者（用于更新对话列表）
        self.notify_sender_via_websocket(message)
    
    def send_message_via_websocket(self, message):
        """通过WebSocket发送消息给接收者。"""
        if not channel_layer:
            return
        
        receiver_group = f"chat_user_{message.receiver.id}"
        message_data = ChatMessageSerializer(message).data
        
        async_to_sync(channel_layer.group_send)(
            receiver_group,
            {
                'type': 'chat_message',
                'message': {
                    'type': 'new_message',
                    'data': message_data,
                }
            }
        )
    
    def notify_sender_via_websocket(self, message):
        """通知发送者消息已发送（用于更新对话列表）。"""
        if not channel_layer:
            return
        
        sender_group = f"chat_user_{message.sender.id}"
        message_data = ChatMessageSerializer(message).data
        
        async_to_sync(channel_layer.group_send)(
            sender_group,
            {
                'type': 'chat_message',
                'message': {
                    'type': 'message_sent',
                    'data': message_data,
                }
            }
        )

    @action(detail=False, methods=['get'])
    def conversations(self, request):
        """获取当前用户的所有对话列表（每个用户只显示一条最新消息）。"""
        user = request.user
        
        # 获取所有与当前用户有消息往来的用户ID
        user_ids = ChatMessage.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).values_list('sender_id', 'receiver_id').distinct()
        
        # 收集所有相关用户ID（排除自己）
        related_user_ids = set()
        for sender_id, receiver_id in user_ids:
            if sender_id != user.id:
                related_user_ids.add(sender_id)
            if receiver_id != user.id:
                related_user_ids.add(receiver_id)
        
        if not related_user_ids:
            return Response([])
        
        # 获取每个用户的最新消息和未读数
        conversations = []
        for other_user_id in related_user_ids:
            other_user = User.objects.get(id=other_user_id)
            
            # 获取最新消息
            last_message = ChatMessage.objects.filter(
                Q(sender=user, receiver=other_user) | Q(sender=other_user, receiver=user)
            ).order_by('-created_at').first()
            
            # 获取未读消息数（对方发给我的未读消息）
            unread_count = ChatMessage.objects.filter(
                sender=other_user,
                receiver=user,
                is_read=False
            ).count()
            
            conversations.append({
                'user_id': other_user.id,
                'username': other_user.username,
                'last_message': last_message.content if last_message else None,
                'last_message_time': last_message.created_at if last_message else None,
                'unread_count': unread_count,
            })
        
        # 按最后消息时间排序
        conversations.sort(key=lambda x: x['last_message_time'] or timezone.now(), reverse=True)
        
        serializer = UserChatSummarySerializer(conversations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def with_user(self, request):
        """获取与指定用户的所有消息。"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'detail': '缺少 user_id 参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        messages = ChatMessage.objects.filter(
            Q(sender=request.user, receiver=other_user) |
            Q(sender=other_user, receiver=request.user)
        ).select_related('sender', 'receiver').order_by('created_at')
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """标记消息为已读。"""
        message = self.get_object()
        if message.receiver != request.user:
            return Response(
                {'detail': '只能标记自己接收的消息为已读'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.is_read = True
        message.read_at = timezone.now()
        message.save()
        
        return Response({'detail': '已标记为已读'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """标记与指定用户的所有消息为已读。"""
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': '缺少 user_id 参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        updated = ChatMessage.objects.filter(
            sender=other_user,
            receiver=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        # 通知更新未读数
        if channel_layer and updated > 0:
            self.notify_unread_update(request.user, other_user.id)
        
        return Response({'detail': f'已标记 {updated} 条消息为已读'})
    
    def notify_unread_update(self, user, other_user_id):
        """通知用户未读数更新。"""
        if not channel_layer:
            return
        
        # 重新计算未读数
        unread_count = ChatMessage.objects.filter(
            sender_id=other_user_id,
            receiver=user,
            is_read=False
        ).count()
        
        user_group = f"chat_user_{user.id}"
        async_to_sync(channel_layer.group_send)(
            user_group,
            {
                'type': 'chat_notification',
                'notification': {
                    'type': 'unread_update',
                    'user_id': other_user_id,
                    'unread_count': unread_count,
                }
            }
        )
