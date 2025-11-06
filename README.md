# Django Vue AdminX

一个基于 Django REST Framework 和 Vue 3 的现代化后台管理系统，提供完整的 RBAC 权限控制、代码生成器、操作日志、任务调度等企业级功能。

![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)
![Django Version](https://img.shields.io/badge/django-5.2.7-green.svg)
![Vue Version](https://img.shields.io/badge/vue-3.5.22-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ 功能特性

### 🔐 权限管理
- **RBAC 权限控制**：基于角色的访问控制，支持菜单、按钮级别权限
- **数据权限**：支持组织级数据隔离，可按组织、用户过滤数据
- **动态权限**：权限实时生效，无需重启服务
- **权限继承**：角色权限可继承，支持权限组合

### 🎨 系统管理
- **用户管理**：用户增删改查、密码重置、角色分配
- **角色管理**：角色创建、权限分配、菜单绑定
- **菜单管理**：动态菜单树、图标选择、路由配置
- **组织管理**：多级组织架构，支持组织树管理
- **权限管理**：细粒度权限控制，支持 API 级别权限

### 📊 仪表盘
- **系统监控**：实时显示 CPU、内存、磁盘、网络使用情况
- **数据统计**：用户、角色、菜单、权限等数据统计
- **图表展示**：基于 ECharts 的数据可视化
- **操作日志**：最近操作记录展示

### 📝 操作日志
- **自动记录**：中间件自动捕获所有 API 请求
- **详细记录**：记录请求参数、响应数据、IP 地址、User-Agent
- **敏感数据过滤**：自动过滤密码、Token 等敏感信息
- **多维度查询**：支持按用户、操作类型、时间范围等查询

### ⏰ 任务调度
- **定时任务**：基于 APScheduler 的定时任务管理
- **任务管理**：任务的增删改查、立即执行
- **Cron 表达式**：支持标准的 Cron 表达式配置
- **任务状态**：任务启用/禁用、执行状态监控

### 🔧 代码生成器
- **一键生成**：根据模型定义自动生成前后端代码
- **CRUD 完整**：自动生成模型的增删改查接口
- **前端页面**：自动生成 Vue 页面，包含列表、表单、搜索
- **数据权限**：可选启用增强型数据权限控制
- **代码注释**：生成的代码包含完整注释

### 📦 其他功能
- **文件上传**：支持文件上传和管理
- **软删除**：支持数据的软删除和恢复
- **审计字段**：自动记录创建人、创建时间、更新人、更新时间
- **数据分页**：统一的分页接口
- **搜索过滤**：支持多字段搜索和过滤

## 🛠️ 技术栈

### 后端
- **Django 5.2.7** - Web 框架
- **Django REST Framework** - RESTful API 框架
- **django-filter** - 数据过滤
- **django-cors-headers** - 跨域支持
- **APScheduler** - 任务调度
- **psutil** - 系统监控
- **MySQL/SQLite** - 数据库

### 前端
- **Vue 3** - 前端框架
- **Vite** - 构建工具
- **Arco Design** - UI 组件库
- **Vue Router** - 路由管理
- **Vuex** - 状态管理
- **Axios** - HTTP 客户端
- **ECharts** - 数据可视化

## 📁 项目结构

```
django-vue-adminx/
├── backend/                       # 后端项目目录
│   ├── apps/                      # Django 应用目录
│   │   ├── audit/                 # 操作日志应用
│   │   │   ├── models.py          # 操作日志模型
│   │   │   ├── middleware.py      # 日志中间件
│   │   │   ├── serializers.py     # 序列化器
│   │   │   ├── views.py           # 视图集
│   │   │   └── urls.py            # URL 路由
│   │   ├── rbac/                  # RBAC 权限应用
│   │   │   ├── models.py          # 用户、角色、权限模型
│   │   │   ├── permissions.py     # 权限控制类
│   │   │   ├── serializers.py     # 序列化器
│   │   │   ├── views.py           # 视图集
│   │   │   └── management/        # 管理命令
│   │   │       └── commands/
│   │   │           └── init_rbac.py  # RBAC 初始化命令
│   │   ├── codegen/               # 代码生成器应用
│   │   │   ├── views.py           # 代码生成视图
│   │   │   └── templates/         # 代码模板
│   │   │       ├── backend/       # 后端模板
│   │   │       └── frontend/      # 前端模板
│   │   ├── tasks/                 # 任务调度应用
│   │   │   ├── models.py          # 任务模型
│   │   │   ├── scheduler.py       # 调度器
│   │   │   └── views.py           # 视图集
│   │   ├── common/                # 公共应用
│   │   │   ├── models.py          # 基础模型
│   │   │   ├── mixins.py          # Mixin 类
│   │   │   ├── viewsets.py        # 视图集基类
│   │   │   └── pagination.py      # 分页类
│   │   └── curdexample/           # 示例应用
│   ├── django_vue_adminx/         # Django 项目配置
│   │   ├── settings.py            # 项目配置
│   │   ├── urls.py                # 根 URL 配置
│   │   └── wsgi.py                # WSGI 配置
│   ├── requirements.txt            # Python 依赖
│   ├── Dockerfile.backend         # 后端 Dockerfile
│   ├── manage.py                  # Django 管理脚本
│   ├── templates/                 # 模板目录
│   └── media/                     # 媒体文件目录
├── front-end/                     # 前端项目
│   ├── src/
│   │   ├── api/                   # API 接口
│   │   ├── views/                 # 页面组件
│   │   ├── components/            # 公共组件
│   │   ├── layout/                # 布局组件
│   │   ├── router/                # 路由配置
│   │   ├── store/                 # 状态管理
│   │   └── utils/                 # 工具函数
│   ├── package.json               # 依赖配置
│   ├── vite.config.js             # Vite 配置
│   └── Dockerfile                 # 前端 Dockerfile
├── docker-compose.yml             # Docker Compose 配置
├── README.md                      # 项目说明文档
└── DOCKER.md                      # Docker 部署文档
```

## 🚀 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- MySQL 8.0+ (可选，默认使用 SQLite)

### 后端安装

1. **克隆项目**
```bash
git clone <repository-url>
cd django-vue-adminx
```

2. **进入后端目录**
```bash
cd backend
```

3. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

4. **安装依赖**
```bash
pip install -r requirements.txt
```

5. **数据库迁移**
```bash
python manage.py migrate
```

6. **初始化 RBAC 数据**
```bash
python manage.py init_rbac --create-superuser
```

7. **启动开发服务器**
```bash
python manage.py runserver
```

后端服务将在 `http://127.0.0.1:8000` 启动

### 前端安装

1. **进入前端目录**
```bash
cd front-end
```

2. **安装依赖**
```bash
npm install
```

3. **启动开发服务器**
```bash
npm run dev
```

前端服务将在 `http://localhost:5173` 启动

### 默认账号

- **用户名**: `admin`
- **密码**: `admin123`

## 🐳 Docker 部署

### 快速启动

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 访问地址

- **前端**: http://localhost
- **后端 API**: http://localhost:8000
- **数据库**: localhost:3306

详细 Docker 部署说明请查看 [DOCKER.md](./DOCKER.md)

## 📚 开发指南

### 创建新的应用

1. **进入后端目录**
```bash
cd backend
```

2. **创建 Django 应用**
```bash
python manage.py startapp apps/myapp
```

2. **在 settings.py 中注册应用**
```python
INSTALLED_APPS = [
    # ...
    'apps.myapp',
]
```

3. **创建模型、序列化器、视图集**
参考 `apps/curdexample` 作为示例

### 使用代码生成器

1. **访问代码生成器页面**
   - 登录系统后，进入"系统管理" -> "代码生成器"

2. **配置生成参数**
   - 应用名称 (app_label)
   - 模型名称 (model_name)
   - 字段配置（字段名、类型、验证规则等）
   - 是否启用增强型数据权限

3. **生成代码**
   - 点击"生成代码"按钮
   - 系统会自动生成前后端代码

4. **应用生成的代码**
   - 后端代码会自动写入对应应用
   - 前端代码会自动生成并注册路由
   - 菜单和权限会自动创建

### RBAC 权限配置

#### 创建角色

```python
from apps.rbac.models import Role, Permission

# 创建角色
role = Role.objects.create(
    name='编辑',
    code='editor',
    description='内容编辑角色'
)

# 分配权限
permissions = Permission.objects.filter(code__startswith='example:')
role.permissions.set(permissions)
```

#### 权限检查

在视图中使用权限装饰器：

```python
from apps.rbac.permissions import RBACPermission

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [RBACPermission]
    required_permissions = ['myapp:list', 'myapp:create']
```

### 数据权限

继承 `SoftDeleteMixin` 和 `AuditOwnerPopulateMixin` 实现数据权限：

```python
from apps.common.models import BaseAuditModel

class MyModel(BaseAuditModel):
    name = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = '我的模型'
        verbose_name_plural = '我的模型'
```

`BaseAuditModel` 包含：
- `created_by` / `updated_by` - 创建/更新人
- `created_at` / `updated_at` - 创建/更新时间
- `owner_organization` - 所属组织
- `is_deleted` / `deleted_at` - 软删除

## 🔌 API 文档

### 认证接口

#### 登录
```http
POST /api/rbac/auth/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

#### 登出
```http
POST /api/rbac/auth/logout/
```

#### 获取用户信息
```http
GET /api/rbac/auth/user-info/
```

### 用户管理

#### 用户列表
```http
GET /api/rbac/users/?page=1&page_size=20
```

#### 创建用户
```http
POST /api/rbac/users/
Content-Type: application/json

{
  "username": "user1",
  "email": "user1@example.com",
  "password": "password123"
}
```

### 角色管理

#### 角色列表
```http
GET /api/rbac/roles/
```

#### 分配角色
```http
POST /api/rbac/users/{id}/roles/
Content-Type: application/json

{
  "role_ids": [1, 2]
}
```

### 操作日志

#### 日志列表
```http
GET /api/audit/logs/?username=admin&action_type=create&created_at_after=2024-01-01
```

#### 日志详情
```http
GET /api/audit/logs/{id}/
```

## 🎯 核心功能说明

### RBAC 权限系统

系统采用基于角色的访问控制（RBAC）模型：

1. **用户 (User)** - 系统用户
2. **角色 (Role)** - 角色定义，可分配多个权限
3. **权限 (Permission)** - 细粒度权限，对应 API 端点
4. **菜单 (Menu)** - 菜单树，可绑定权限
5. **组织 (Organization)** - 组织架构，用于数据权限

权限检查流程：
1. 用户登录后获取角色和权限列表
2. 前端根据权限动态显示菜单和按钮
3. 后端 API 请求时检查用户是否拥有对应权限
4. 数据权限根据用户的组织范围过滤数据

### 代码生成器

代码生成器支持：

1. **模型代码生成**
   - 自动生成 Django 模型
   - 支持常用字段类型
   - 自动添加审计字段

2. **后端代码生成**
   - ViewSet 视图集
   - Serializer 序列化器
   - URL 路由配置
   - 可选增强型数据权限

3. **前端代码生成**
   - Vue 页面组件
   - API 接口文件
   - 自动注册路由
   - 自动创建菜单

### 操作日志

操作日志中间件自动记录：

- 请求方法、路径、参数
- 响应状态码、数据
- 用户信息、IP 地址
- 操作时间
- 错误信息（如果有）

敏感数据（密码、Token 等）会自动过滤。

### 任务调度

基于 APScheduler 实现：

- 支持 Cron 表达式
- 任务启用/禁用
- 立即执行任务
- 任务状态监控

## ❓ 常见问题

### 1. 登录后无法访问页面

**问题**: 登录成功但页面空白或提示无权限

**解决**:
- 检查用户是否分配了角色
- 检查角色是否分配了权限
- 检查菜单是否绑定了权限
- 进入 backend 目录，运行 `python manage.py init_rbac` 初始化权限数据

### 2. 前端 API 请求失败

**问题**: 前端调用 API 返回 403 或 401

**解决**:
- 检查是否已登录
- 检查用户是否有对应权限
- 检查 CORS 配置
- 检查 CSRF Token 是否正确传递

### 3. 代码生成器生成失败

**问题**: 代码生成器报错或生成代码有语法错误

**解决**:
- 检查应用名称和模型名称是否正确
- 检查字段配置是否完整
- 查看后端日志获取详细错误信息

### 4. Docker 部署后无法访问

**问题**: Docker 启动后无法访问服务

**解决**:
- 检查端口是否被占用
- 检查防火墙设置
- 查看容器日志: `docker-compose logs`
- 检查数据库连接配置

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👥 作者

- **Your Name** - *Initial work*

## 🙏 致谢

- [Django](https://www.djangoproject.com/) - Web 框架
- [Django REST Framework](https://www.django-rest-framework.org/) - RESTful API 框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [Arco Design](https://arco.design/) - UI 组件库
- [APScheduler](https://apscheduler.readthedocs.io/) - 任务调度库

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**



