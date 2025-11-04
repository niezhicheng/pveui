from rest_framework.routers import DefaultRouter
from .views_${model_name} import ${ModelName}ViewSet


router = DefaultRouter()
router.register(r'${model_name}', ${ModelName}ViewSet, basename='${model_name}')

urlpatterns = router.urls

