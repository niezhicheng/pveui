"""操作日志中间件：自动记录 API 请求操作。"""

import json
import logging
from typing import Any, Dict

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from .models import OperationLog

logger = logging.getLogger(__name__)


class OperationLogMiddleware(MiddlewareMixin):
    """操作日志中间件：自动记录 API 请求。

    记录规则：
    - 只记录 API 请求（/api/ 开头）
    - 排除登录、登出、静态文件等
    - 记录请求参数、响应状态、错误信息
    - 自动识别操作类型（根据 HTTP 方法）
    """

    # 排除的路径（不记录日志）
    EXCLUDE_PATHS = [
        '/api/rbac/login/',
        '/api/rbac/logout/',
        '/api/rbac/system/metrics/',
        '/api/rbac/system/menu/tree/',
        '/api/rbac/system/organization/tree/',
    ]

    # HTTP 方法到操作类型的映射
    METHOD_TO_ACTION = {
        'GET': OperationLog.ACTION_VIEW,
        'POST': OperationLog.ACTION_CREATE,
        'PUT': OperationLog.ACTION_UPDATE,
        'PATCH': OperationLog.ACTION_UPDATE,
        'DELETE': OperationLog.ACTION_DELETE,
    }

    def process_request(self, request):
        """处理请求前：准备日志数据。"""
        # 只记录 API 请求
        if not request.path.startswith('/api/'):
            return None

        # 排除的路径
        if any(request.path.startswith(path) for path in self.EXCLUDE_PATHS):
            return None

        # 记录请求信息到 request
        request._operation_log = {
            'request_path': request.path,
            'request_method': request.method,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
            'request_params': self._extract_request_params(request),
            'action_type': self.METHOD_TO_ACTION.get(request.method, OperationLog.ACTION_OTHER),
        }

        # 如果是列表请求，标记为 list
        if request.method == 'GET' and not any(
            request.path.endswith(f'/{pk}/') for pk in request.path.split('/') if pk.isdigit()
        ):
            request._operation_log['action_type'] = OperationLog.ACTION_LIST

        return None

    def process_response(self, request, response):
        """处理响应后：记录日志。"""
        # 检查是否有日志数据
        if not hasattr(request, '_operation_log'):
            return response

        try:
            # 获取用户信息
            user = getattr(request, 'user', None)
            username = ''
            if user and hasattr(user, 'is_authenticated') and user.is_authenticated:
                username = getattr(user, 'username', '') or str(user)

            # 提取操作对象信息（如果有）
            content_type = None
            object_id = None
            object_repr = ''

            # 尝试从响应数据中提取对象信息
            if hasattr(response, 'data') and isinstance(response.data, dict):
                # 如果是单对象响应，提取对象信息
                obj_data = response.data.get('data') or response.data
                if isinstance(obj_data, dict) and 'id' in obj_data:
                    object_id = obj_data.get('id')
                    # 尝试从 URL 推断模型
                    path_parts = request.path.strip('/').split('/')
                    if len(path_parts) >= 3:
                        app_label = path_parts[1]
                        model_name = path_parts[2].rstrip('s')  # 去掉复数形式
                        try:
                            # 尝试获取 ContentType
                            from django.apps import apps
                            app_config = apps.get_app_config(app_label)
                            model = app_config.get_model(model_name, None)
                            if model:
                                content_type = ContentType.objects.get_for_model(model)
                                # 尝试获取对象描述
                                try:
                                    obj = model.objects.get(pk=object_id)
                                    object_repr = str(obj)[:255]
                                except Exception:
                                    pass
                        except Exception:
                            pass

            # 记录日志
            OperationLog.objects.create(
                user=user if (user and hasattr(user, 'is_authenticated') and user.is_authenticated) else None,
                username=username,
                action_type=request._operation_log['action_type'],
                content_type=content_type,
                object_id=object_id,
                object_repr=object_repr,
                request_path=request._operation_log['request_path'],
                request_method=request._operation_log['request_method'],
                request_params=request._operation_log['request_params'],
                ip_address=request._operation_log['ip_address'],
                user_agent=request._operation_log['user_agent'],
                status_code=response.status_code,
                error_message=self._extract_error_message(response) if response.status_code >= 400 else '',
            )
        except Exception as e:
            # 记录日志失败不影响正常请求
            logger.warning(f'Failed to create operation log: {e}', exc_info=True)

        return response

    def _get_client_ip(self, request) -> str:
        """获取客户端 IP 地址。"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip[:45]  # IP 地址最大长度

    def _extract_request_params(self, request) -> Dict[str, Any]:
        """提取请求参数。"""
        params = {}

        # GET 参数
        if request.GET:
            params['query'] = dict(request.GET)

        # POST/PUT/PATCH 参数
        if request.method in ('POST', 'PUT', 'PATCH'):
            try:
                # 尝试从 request.body 解析 JSON
                if hasattr(request, 'body') and request.body:
                    try:
                        body_data = json.loads(request.body)
                        # 过滤敏感信息
                        filtered_data = self._filter_sensitive_data(body_data)
                        params['body'] = filtered_data
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # 如果不是 JSON，尝试 form data
                        if hasattr(request, 'POST'):
                            params['body'] = dict(request.POST)
            except Exception:
                pass

        return params

    def _filter_sensitive_data(self, data: Any, max_depth: int = 3) -> Any:
        """过滤敏感信息（密码、token 等）。"""
        sensitive_keys = {'password', 'pwd', 'token', 'secret', 'key', 'api_key', 'access_token'}

        if isinstance(data, dict):
            if max_depth <= 0:
                return '[MAX_DEPTH]'
            filtered = {}
            for k, v in data.items():
                if any(sk in k.lower() for sk in sensitive_keys):
                    filtered[k] = '***'
                else:
                    filtered[k] = self._filter_sensitive_data(v, max_depth - 1)
            return filtered
        elif isinstance(data, list):
            if max_depth <= 0:
                return '[MAX_DEPTH]'
            return [self._filter_sensitive_data(item, max_depth - 1) for item in data]
        else:
            return data

    def _extract_error_message(self, response) -> str:
        """提取错误信息。"""
        if hasattr(response, 'data') and isinstance(response.data, dict):
            error_msg = response.data.get('detail') or response.data.get('message') or str(response.data)
            return str(error_msg)[:1000]  # 限制长度
        return ''

