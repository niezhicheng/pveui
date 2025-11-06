from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ${ModelName}ViewSet


# 该文件可独立作为 app 的路由入口
router = DefaultRouter()
router.register(r'${model_name}', ${ModelName}ViewSet, basename='${model_name}')

urlpatterns = [
    path('', include(router.urls)),
]

