"""客服系统 WebSocket 路由。"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/customer-service/guest/(?P<session_id>[\w-]+)/(?P<token>[\w-]+)/$',
        consumers.GuestSessionConsumer.as_asgi()
    ),
]


