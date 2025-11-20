"""客服系统 WebSocket 消费者。"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import GuestSession


class GuestSessionConsumer(AsyncWebsocketConsumer):
    """访客会话 WebSocket：向访客推送消息。"""

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.secret_token = self.scope['url_route']['kwargs']['token']

        self.session = await self.get_session()
        if not self.session:
            await self.close()
            return

        self.group_name = f"cs_session_{self.session.session_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # 访客端目前不通过 WebSocket 发送消息（使用 REST 接口），这里只保留心跳
        try:
            if text_data:
                data = json.loads(text_data)
                if data.get('type') == 'ping':
                    await self.send(text_data=json.dumps({'type': 'pong'}))
        except json.JSONDecodeError:
            pass

    async def session_message(self, event):
        """向访客发送消息事件。"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'data': event['message'],
        }))

    @database_sync_to_async
    def get_session(self):
        try:
            return GuestSession.objects.get(session_id=self.session_id, secret_token=self.secret_token)
        except GuestSession.DoesNotExist:
            return None


