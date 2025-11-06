# Docker 部署说明

## 快速开始

### 1. 构建并启动所有服务

```bash
docker-compose up -d
```

### 2. 查看服务状态

```bash
docker-compose ps
```

### 3. 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### 4. 停止服务

```bash
docker-compose down
```

### 5. 停止并删除数据卷（谨慎操作）

```bash
docker-compose down -v
```

## 服务说明

### 后端服务 (backend)
- **端口**: 8000
- **镜像**: 基于 `python:3.12-slim`
- **Web 服务器**: Gunicorn (4 workers)
- **数据库迁移**: 自动执行
- **RBAC 初始化**: 自动执行（如果不存在）

### 前端服务 (frontend)
- **端口**: 80
- **镜像**: 基于 `nginx:alpine`
- **构建**: 多阶段构建（Node.js + Nginx）
- **API 代理**: `/api/` 路径自动代理到后端

### 数据库服务 (db)
- **类型**: MySQL 8.0
- **端口**: 3306
- **数据库名**: django_vue_adminx
- **用户名**: django
- **密码**: django123
- **Root 密码**: root123

## 环境变量

可以通过 `.env` 文件或环境变量配置：

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
DB_NAME=django_vue_adminx
DB_USER=django
DB_PASSWORD=django123
DB_HOST=db
DB_PORT=3306
```

## 数据持久化

Docker Compose 使用数据卷持久化以下数据：
- `mysql_data`: MySQL 数据库数据
- `static_volume`: Django 静态文件
- `media_volume`: Django 媒体文件

## 常用命令

### 进入容器

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入数据库容器
docker-compose exec db mysql -u django -pdjango123 django_vue_adminx
# 或使用 root 用户
docker-compose exec db mysql -u root -proot123 django_vue_adminx
```

### 执行 Django 管理命令

```bash
# 创建超级用户
docker-compose exec backend python manage.py createsuperuser

# 执行数据库迁移
docker-compose exec backend python manage.py migrate

# 初始化 RBAC
docker-compose exec backend python manage.py init_rbac

# 收集静态文件
docker-compose exec backend python manage.py collectstatic
```

**注意**: 所有后端管理命令都在容器内执行，工作目录为 `/app`（对应本地的 `backend/` 目录）

### 重建服务

```bash
# 重新构建并启动
docker-compose up -d --build

# 仅重建特定服务
docker-compose build backend
docker-compose up -d backend
```

## 访问地址

- **前端**: http://localhost
- **后端 API**: http://localhost:8000
- **数据库**: localhost:3306

## 默认账号

首次启动会自动创建超级用户：
- **用户名**: admin
- **密码**: admin123

## 生产环境注意事项

1. **修改 SECRET_KEY**: 使用强随机密钥
2. **修改数据库密码**: 使用强密码
3. **配置 HTTPS**: 使用反向代理（如 Traefik、Nginx）
4. **设置 ALLOWED_HOSTS**: 在 settings.py 中配置
5. **关闭 DEBUG**: 已设置为 False
6. **配置静态文件**: 生产环境建议使用 CDN 或对象存储
7. **监控和日志**: 配置日志收集和监控系统

## 故障排查

### 后端无法连接数据库

检查数据库服务是否正常运行：
```bash
docker-compose ps db
docker-compose logs db
```

如果 MySQL 连接失败，可能需要等待数据库完全初始化（首次启动可能需要 30-60 秒）。

### 前端无法访问后端 API

检查 Nginx 配置和网络连接：
```bash
docker-compose exec frontend nginx -t
docker-compose logs frontend
```

### 权限问题

检查文件权限：
```bash
docker-compose exec backend ls -la /app
```

