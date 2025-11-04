from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from apps.${AppLabel}.models import ${ModelName}
from .serializers_${model_name} import ${ModelName}Serializer


class ${ModelName}ViewSet(viewsets.ModelViewSet):
    queryset = ${ModelName}.objects.all().order_by('-id')
    serializer_class = ${ModelName}Serializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['id']
    ordering_fields = ['id']

