"""
ASGI config for django_vue_adminx project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
# 必须在导入任何模块之前设置环境变量，禁用 autobahn 的 C 扩展
os.environ['AUTOBAHN_USE_UVLOOP'] = '0'
os.environ['TWISTED_REACTOR'] = 'asyncio'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_vue_adminx.settings')

# 在导入 autobahn 相关模块之前，尝试禁用 UTF8 validator 的 C 扩展
try:
    import sys
    # 创建一个假的模块来避免导入 C 扩展
    class FakeModule:
        pass
    sys.modules['_nvx_utf8validator'] = FakeModule()
except Exception:
    pass

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# 初始化Django应用
django_asgi_app = get_asgi_application()

# 导入WebSocket路由
from apps.chat.routing import websocket_urlpatterns as chat_websocket_urlpatterns
from apps.customer_service.routing import websocket_urlpatterns as cs_websocket_urlpatterns

websocket_urlpatterns = chat_websocket_urlpatterns + cs_websocket_urlpatterns

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
