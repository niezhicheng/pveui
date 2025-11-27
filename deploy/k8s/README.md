# Kubernetes 部署说明

## 前置要求

- Kubernetes 集群（1.20+）
- kubectl 已配置并连接到集群
- Docker 镜像已构建并推送到镜像仓库（或使用本地镜像）

## 部署步骤

### 1. 创建命名空间

```bash
kubectl apply -f namespace.yaml
```

### 2. 创建配置和密钥

```bash
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
```

**注意**: 生产环境请修改 `secret.yaml` 中的敏感信息！

### 3. 部署 MySQL

```bash
kubectl apply -f mysql.yaml
```

等待 MySQL Pod 就绪：
```bash
kubectl wait --for=condition=ready pod -l app=mysql -n pve-ui --timeout=300s
```

### 4. 部署后端

```bash
kubectl apply -f backend.yaml
```

### 5. 部署前端

```bash
kubectl apply -f frontend.yaml
```

### 6. 部署 Ingress（可选）

如果需要外部访问：

```bash
kubectl apply -f ingress.yaml
```

修改 `ingress.yaml` 中的 `host` 为你的域名。

### 7. 创建媒体文件 PVC（如果需要）

```bash
kubectl apply -f media-pvc.yaml
```

## 一键部署

```bash
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f media-pvc.yaml
kubectl apply -f mysql.yaml
kubectl wait --for=condition=ready pod -l app=mysql -n pve-ui --timeout=300s
kubectl apply -f backend.yaml
kubectl apply -f frontend.yaml
kubectl apply -f ingress.yaml
```

## 构建和推送镜像

### 构建镜像

```bash
# 后端镜像
docker build -f deploy/Dockerfile.backend -t pve-ui-backend:latest backend/

# 前端镜像
docker build -f deploy/Dockerfile.frontend -t pve-ui-frontend:latest .
```

### 推送到镜像仓库

```bash
# 替换为你的镜像仓库地址
docker tag pve-ui-backend:latest your-registry/pve-ui-backend:latest
docker tag pve-ui-frontend:latest your-registry/pve-ui-frontend:latest

docker push your-registry/pve-ui-backend:latest
docker push your-registry/pve-ui-frontend:latest
```

### 更新 YAML 文件中的镜像地址

修改 `backend.yaml` 和 `frontend.yaml` 中的 `image` 字段为你的镜像地址。

## 查看状态

```bash
# 查看所有资源
kubectl get all -n pve-ui

# 查看 Pod 状态
kubectl get pods -n pve-ui

# 查看服务
kubectl get svc -n pve-ui

# 查看日志
kubectl logs -f deployment/backend -n pve-ui
kubectl logs -f deployment/frontend -n pve-ui
```

## 删除部署

```bash
kubectl delete namespace pve-ui
```

## 配置说明

### ConfigMap

存储非敏感配置：
- `DEBUG`: 调试模式
- `DB_NAME`: 数据库名
- `DB_USER`: 数据库用户
- `DB_HOST`: 数据库主机
- `DB_PORT`: 数据库端口

### Secret

存储敏感信息：
- `SECRET_KEY`: Django 密钥
- `DB_PASSWORD`: 数据库密码
- `MYSQL_ROOT_PASSWORD`: MySQL root 密码

### 持久化存储

- `mysql-pvc`: MySQL 数据持久化（10Gi）
- `media-pvc`: 媒体文件持久化（5Gi，ReadWriteMany）

## 扩展

### 水平扩展

```bash
# 扩展后端副本数
kubectl scale deployment backend --replicas=3 -n pve-ui

# 扩展前端副本数
kubectl scale deployment frontend --replicas=3 -n pve-ui
```

### 资源限制

可以在 Deployment 中添加资源限制：

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

## 常见问题

### 1. Pod 无法启动

检查 Pod 状态和日志：
```bash
kubectl describe pod <pod-name> -n pve-ui
kubectl logs <pod-name> -n pve-ui
```

### 2. 数据库连接失败

确保 MySQL Pod 已就绪：
```bash
kubectl get pods -l app=mysql -n pve-ui
```

### 3. 无法访问服务

检查 Service 和 Ingress：
```bash
kubectl get svc -n pve-ui
kubectl get ingress -n pve-ui
```

