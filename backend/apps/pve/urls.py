"""PVE模块URL路由。"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PVEServerViewSet, VirtualMachineViewSet

router = DefaultRouter()
router.register(r'servers', PVEServerViewSet, basename='pve-server')
router.register(r'virtual-machines', VirtualMachineViewSet, basename='virtual-machine')

urlpatterns = [
    path('', include(router.urls)),
]

