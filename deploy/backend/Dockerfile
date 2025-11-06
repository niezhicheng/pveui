# Django 后端 Dockerfile
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖（MySQL 客户端和 mysqlclient 编译依赖）
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    mysql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements 文件（从 backend 目录）
COPY backend/requirements.txt /app/

# 安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制项目代码（从 backend 目录）
COPY backend/ /app/

# 收集静态文件（如果需要）
RUN python manage.py collectstatic --noinput || true

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "django_vue_adminx.wsgi:application"]

