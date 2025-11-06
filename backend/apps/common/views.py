"""通用业务接口：文件上传等。"""

import os
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response


class FileUploadView(APIView):
    """文件上传接口：支持图片、文档等。

    Request: multipart/form-data, field name: 'file'
    Response: { "url": "/media/uploads/xxx.jpg", "filename": "xxx.jpg" }
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):  # noqa: D401
        if 'file' not in request.FILES:
            return Response({"detail": "未找到文件"}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['file']
        if uploaded_file.size == 0:
            return Response({"detail": "文件为空"}, status=status.HTTP_400_BAD_REQUEST)

        # 限制文件大小（默认 10MB）
        max_size = 10 * 1024 * 1024
        if uploaded_file.size > max_size:
            return Response({"detail": f"文件大小超过限制（{max_size // 1024 // 1024}MB）"}, status=status.HTTP_400_BAD_REQUEST)

        # 生成保存路径
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        # 生成唯一文件名
        import uuid
        ext = os.path.splitext(uploaded_file.name)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(upload_dir, filename)

        # 保存文件
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # 返回相对 URL
        relative_url = os.path.join(settings.MEDIA_URL, 'uploads', filename).replace('\\', '/')
        return Response({
            "url": relative_url,
            "filename": filename,
            "original_name": uploaded_file.name,
            "size": uploaded_file.size,
        })

