"""聊天模块路由。"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatMessageViewSet

router = DefaultRouter()
router.register(r'messages', ChatMessageViewSet, basename='chat-message')

urlpatterns = [
    path('', include(router.urls)),
]

