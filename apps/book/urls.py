from .views import BookViewSet
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'book', BookViewSet, basename='book')
urlpatterns = [
    path('', include(router.urls)),
]
