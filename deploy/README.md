# 部署文件说明

本目录包含项目的所有部署相关配置文件。

## 目录结构

```
deploy/
├── Dockerfile.backend          # 后端 Dockerfile
├── Dockerfile.frontend          # 前端 Dockerfile
├── docker-compose.yml           # Docker Compose 配置
├── nginx.conf                   # Nginx 配置文件
├── k8s/                        # Kubernetes 配置文件
│   ├── namespace.yaml          # 命名空间
│   ├── configmap.yaml          # 配置映射
│   ├── secret.yaml             # 密钥
│   ├── mysql.yaml              # MySQL 部署
│   ├── backend.yaml            # 后端部署
│   ├── frontend.yaml           # 前端部署
│   ├── ingress.yaml            # Ingress 配置
│   ├── media-pvc.yaml          # 媒体文件持久卷
│   └── README.md               # K8s 部署说明
└── README.md                    # 本文件
```

## Docker 部署

### 使用 Docker Compose

```bash
cd deploy
docker-compose up -d
```

或从项目根目录：

```bash
docker-compose -f deploy/docker-compose.yml up -d
```

### 单独构建镜像

```bash
# 构建后端镜像
docker build -f deploy/Dockerfile.backend -t pve-ui-backend:latest backend/

# 构建前端镜像
docker build -f deploy/Dockerfile.frontend -t pve-ui-frontend:latest .
```

## Kubernetes 部署

详细说明请查看 [k8s/README.md](./k8s/README.md)

快速部署：

```bash
cd k8s
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

## 注意事项

1. **生产环境**: 请务必修改 `k8s/secret.yaml` 中的敏感信息
2. **镜像仓库**: K8s 部署需要将镜像推送到可访问的镜像仓库
3. **存储**: 根据实际需求调整 PVC 的大小和类型
4. **域名**: 修改 `k8s/ingress.yaml` 中的域名配置

