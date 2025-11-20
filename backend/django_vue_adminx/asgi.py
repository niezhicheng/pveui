"""
ASGI config for django_vue_adminx project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_vue_adminx.settings')

# 初始化Django应用
django_asgi_app = get_asgi_application()

# 导入WebSocket路由
from apps.chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    # HTTP请求使用Django ASGI应用
    "http": django_asgi_app,
    
    # WebSocket请求使用自定义路由
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
