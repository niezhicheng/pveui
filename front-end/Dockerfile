# Vue 前端 Dockerfile（多阶段构建）
ARG FRONTEND_DIR=front-end

# 阶段1: 构建阶段
FROM node:22-alpine AS builder

WORKDIR /app

# 复制源代码
COPY ./ ./

RUN npm config set registry https://registry.npmmirror.com
RUN npm install
RUN npm install @novnc/novnc@1.4.0
# 构建生产版本
RUN npm run build

# 阶段2: 运行阶段（使用 Nginx）
FROM nginx:alpine

# 复制构建产物到 Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY  --from=builder /app/nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
