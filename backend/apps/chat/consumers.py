"""WebSocket消费者：处理聊天消息的实时通信。"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import ChatMessage

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """聊天WebSocket消费者。"""

    async def connect(self):
        """WebSocket连接建立时调用。"""
        self.user = self.scope["user"]
        
        # 如果用户未认证，拒绝连接
        if not self.user.is_authenticated:
            await self.close()
            return

        # 为每个用户创建一个个人频道组
        self.user_group_name = f"chat_user_{self.user.id}"
        
        # 将用户添加到个人频道组
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        """WebSocket断开连接时调用。"""
        # 从频道组中移除
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """接收到WebSocket消息时调用。"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # 心跳检测
                await self.send(text_data=json.dumps({
                    'type': 'pong'
                }))
            elif message_type == 'mark_read':
                # 标记消息为已读
                user_id = data.get('user_id')
                if user_id:
                    await self.mark_all_read(user_id)
        except json.JSONDecodeError:
            pass

    async def chat_message(self, event):
        """接收频道组消息并发送给WebSocket客户端。"""
        message = event['message']
        await self.send(text_data=json.dumps(message))

    async def chat_notification(self, event):
        """接收通知消息（如未读数更新）。"""
        notification = event['notification']
        await self.send(text_data=json.dumps(notification))

    @database_sync_to_async
    def mark_all_read(self, user_id):
        """标记与指定用户的所有消息为已读。"""
        try:
            other_user = User.objects.get(id=user_id)
            ChatMessage.objects.filter(
                sender=other_user,
                receiver=self.user,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())
        except User.DoesNotExist:
            pass

