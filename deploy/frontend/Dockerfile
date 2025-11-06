# Vue 前端 Dockerfile（多阶段构建）
ARG FRONTEND_DIR=front-end

# 阶段1: 构建阶段
FROM node:20-alpine AS builder

WORKDIR /app

# 复制 package 文件
COPY ${FRONTEND_DIR}/package*.json ./

# 安装依赖
RUN npm ci --only=production=false

# 复制源代码
COPY ${FRONTEND_DIR}/ ./

# 构建生产版本
RUN npm run build

# 阶段2: 运行阶段（使用 Nginx）
FROM nginx:alpine

# 复制构建产物到 Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY deploy/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]

