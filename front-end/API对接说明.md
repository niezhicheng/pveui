# 前端与后端 API 对接说明

## 已完成对接

### 1. 登录接口
- **后端接口**: `POST /api/rbac/auth/login/`
- **前端调用**: `src/api/user.js` 中的 `login()` 函数
- **认证方式**: Django Session（通过 Cookie）

### 2. 退出登录接口
- **后端接口**: `POST /api/rbac/auth/logout/`
- **前端调用**: `src/api/user.js` 中的 `logout()` 函数

### 3. 获取用户信息接口
- **后端接口**: `GET /api/rbac/auth/user-info/`
- **前端调用**: `src/api/user.js` 中的 `getUserInfo()` 函数

## 配置说明

### 1. 环境变量配置
在 `front-end` 目录下创建 `.env.development` 文件（开发环境）：
```env
VITE_HOST=http://127.0.0.1:8000
```

创建 `.env.production` 文件（生产环境）：
```env
VITE_HOST=http://127.0.0.1:8000
```

如果没有设置环境变量，默认使用 `http://127.0.0.1:8000`

### 2. 后端配置
- ✅ 已配置 `CORS_ALLOW_CREDENTIALS = True` 支持 Cookie
- ✅ 已配置 `CORS_ORIGIN_ALLOW_ALL = True` 允许跨域

## 修改的文件

### 前端文件
1. **`src/utils/request.js`**
   - 添加 `withCredentials: true` 支持 Cookie
   - 改进错误处理
   - 默认 baseURL 为 `http://127.0.0.1:8000`

2. **`src/api/user.js`**
   - 修改登录接口路径为 `/api/rbac/auth/login/`
   - 修改退出接口路径为 `/api/rbac/auth/logout/`
   - 新增获取用户信息接口

3. **`src/store/modules/user.js`**
   - 移除 Token 存储逻辑（改为 Session 认证）
   - 保存用户信息到 state
   - 新增 `getUserInfo` action
   - 新增权限和角色检查的 getters

4. **`src/permission.js`**
   - 改为通过检查用户信息判断登录状态
   - 自动调用 `getUserInfo` 验证 Session

### 后端文件
1. **`django_vue_adminx/settings.py`**
   - 添加 `CORS_ALLOW_CREDENTIALS = True`

## 使用说明

### 启动后端
```bash
cd /Users/niezhicheng/PycharmProjects/pve-ui
python manage.py runserver
```

### 启动前端
```bash
cd front-end
npm install  # 如果还没安装依赖
npm run dev
```

### 测试登录
1. 访问前端登录页面（通常是 `http://localhost:5173` 或类似端口）
2. 使用默认账号：`admin` / `admin123`（如果已运行初始化脚本）
3. 或使用 Django 创建的超级用户账号

## 注意事项

1. **Cookie 同源策略**: 确保前端和后端在同一域名下，或正确配置 CORS
2. **CSRF Token**: DRF APIView 默认会绕过 CSRF 检查，如果遇到问题可以添加 `@csrf_exempt` 装饰器
3. **Session 过期**: 如果 Session 过期，前端会自动跳转到登录页

## 后续需要对接的接口

- [ ] 菜单树接口：`GET /api/rbac/menu-tree/`
- [ ] 权限检查接口：`POST /api/rbac/auth/check-permission/`
- [ ] 其他业务接口...

