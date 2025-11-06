from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.tasks.views import JobViewSet

router = DefaultRouter()
router.register(r'tasks', JobViewSet, basename='tasks')

urlpatterns = [
	path('', include(router.urls)),
]

