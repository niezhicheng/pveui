"""通用业务路由：文件上传等。"""

from django.urls import path
from .views import FileUploadView

urlpatterns = [
    path('upload/', FileUploadView.as_view()),
]

