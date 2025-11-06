from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from django.conf import settings
from django.utils.text import slugify
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


def write_file_safe(target: Path, content: str) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target = target.with_suffix(target.suffix + '.gen')
    target.write_text(content, encoding='utf-8')
    return target


def build_model_code(app_label: str, model_name: str, fields: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("from django.db import models")
    lines.append("from apps.common.models import BaseAuditModel")
    lines.append("")
    lines.append(f"class {model_name}(BaseAuditModel):")
    lines.append("    # 自动生成的业务模型")
    lines.append("    # 说明：继承 BaseAuditModel，包含审计与归属字段（created_by/updated_by/owner_organization）。")
    lines.append("    # 可按需调整字段、添加索引/约束，或补充 __str__/Meta 配置。")
    if not fields:
        lines.append("    pass")
    else:
        for f in fields:
            name = f.get('name')
            ftype = f.get('type')
            required = f.get('required', True)
            unique = f.get('unique', False)
            verbose_name = f.get('verbose_name') or name
            default = f.get('default', None)

            args: List[str] = []
            if ftype == 'CharField':
                args.append(f"max_length={int(f.get('max_length', 128))}")
            elif ftype == 'DecimalField':
                args.append(f"max_digits={int(f.get('max_digits', 10))}")
                args.append(f"decimal_places={int(f.get('decimal_places', 2))}")
            elif ftype == 'ForeignKey':
                related_app = f.get('related_app')
                related_model = f.get('related_model')
                if not related_app or not related_model:
                    raise ValueError('ForeignKey 需要 related_app 与 related_model')
                args.append(f"'apps.{related_app}.{related_model}'")
                args.append("on_delete=models.PROTECT")

            # Common kwargs
            if not required:
                args.append("null=True")
                args.append("blank=True")
            if unique:
                args.append("unique=True")
            if default not in (None, ""):
                # Render Python literal for default: True/False numbers/strings
                if isinstance(default, bool):
                    lit = 'True' if default else 'False'
                elif isinstance(default, (int, float)):
                    lit = repr(default)
                elif isinstance(default, str):
                    # simple quote; no escaping strategy here for brevity
                    lit = f"'{default}'"
                else:
                    # fallback to repr
                    lit = repr(default)
                args.append(f"default={lit}")
            if verbose_name:
                args.append(f"verbose_name='{verbose_name}'")

            if ftype == 'ForeignKey':
                field_expr = f"models.ForeignKey({', '.join(args)})"
            else:
                field_expr = f"models.{ftype}({', '.join(args)})"

            lines.append(f"    {name} = {field_expr}")

    # Optional Meta and __str__
    lines.append("")
    lines.append("    class Meta:")
    lines.append(f"        verbose_name = '{model_name}'")
    lines.append(f"        verbose_name_plural = '{model_name}'")
    lines.append("")
    # Use first char/text field as __str__ if present
    str_field = next((f['name'] for f in fields if f.get('type') in ('CharField', 'TextField')), None)
    if str_field:
        lines.append("    def __str__(self) -> str:")
        lines.append(f"        return str(self.{str_field})")
    else:
        lines.append("    def __str__(self) -> str:")
        lines.append("        return f'<%s %s>' % (self.__class__.__name__, self.pk)")

    return "\n".join(lines) + "\n"


class GenerateFromSpecView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data or {}
        app_label = data.get('app_label')
        model_name = data.get('model_name')
        module_path = data.get('module_path') or f"{app_label}/{str(model_name).lower()}"
        fields = data.get('fields') or []
        enhanced = bool(data.get('enhanced_data_scope'))

        if not app_label or not model_name:
            return Response({'detail': 'app_label 与 model_name 必填'}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(fields, list) or not fields:
            return Response({'detail': 'fields 需为非空数组'}, status=status.HTTP_400_BAD_REQUEST)

        base_dir = Path(settings.BASE_DIR)  # backend/ 目录
        # 前端在项目根目录，需要向上跳一级
        project_root = base_dir.parent  # 项目根目录
        app_dir = base_dir / 'apps' / app_label
        if not app_dir.exists():
            # 自动创建最小 Django 应用结构，并尝试写入 INSTALLED_APPS
            try:
                app_dir.mkdir(parents=True, exist_ok=True)
                (app_dir / '__init__.py').write_text('', encoding='utf-8')
                app_config_name = f"{app_label.capitalize()}Config"
                (app_dir / 'apps.py').write_text(
                    "from django.apps import AppConfig\n\n"
                    f"class {app_config_name}(AppConfig):\n"
                    f"    default_auto_field = 'django.db.models.BigAutoField'\n"
                    f"    name = 'apps.{app_label}'\n",
                    encoding='utf-8'
                )
                for fname, content in [
                    ('models.py', 'from django.db import models\n'),
                    ('admin.py', ''),
                    ('views.py', ''),
                    ('urls.py', 'from django.urls import path, include\nfrom rest_framework.routers import DefaultRouter\n\nrouter = DefaultRouter()\n\nurlpatterns = [\n    path(\'\', include(router.urls)),\n]\n'),
                    ('migrations/__init__.py', ''),
                ]:
                    target = app_dir / fname
                    if target.parent.name == 'migrations':
                        target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content, encoding='utf-8')

                settings_file = base_dir / 'django_vue_adminx' / 'settings.py'
                try:
                    text = settings_file.read_text(encoding='utf-8')
                    if f"'apps.{app_label}'" not in text and f'"apps.{app_label}"' not in text:
                        import re
                        m = re.search(r"INSTALLED_APPS\s*=\s*\[(.*?)\]", text, re.S)
                        if m:
                            body = m.group(1)
                            before = text[:m.start(1)]
                            after = text[m.end(1):]
                            new_entry = f"\n    'apps.{app_label}'\n"
                            stripped = body.strip()
                            if not stripped:
                                new_body = new_entry
                            else:
                                if stripped.endswith(','):
                                    new_body = body + new_entry
                                else:
                                    new_body = body.rstrip() + "," + new_entry
                            new_text = before + new_body + after
                            settings_file.write_text(new_text, encoding='utf-8')
                except Exception:
                    pass
            except Exception as e:
                return Response({'detail': f'自动创建应用失败: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 1) 将模型类直接追加到 apps/<app>/models.py（若已存在同名类可手动处理）
        model_code = build_model_code(app_label, model_name, fields)
        models_py = app_dir / 'models.py'
        if not models_py.exists():
            models_py.write_text('from django.db import models\n', encoding='utf-8')
        with models_py.open('a', encoding='utf-8') as f:
            f.write('\n\n')
            f.write(model_code)

        # 2) 生成后端 serializers/views 到 app 的标准文件（无前缀），urls 注入 router.register
        try:
            from string import Template
            templates_dir = base_dir / 'apps' / 'codegen' / 'templates'

            def load(rel: str) -> Template:
                return Template((templates_dir / rel).read_text(encoding='utf-8'))

            ctx = {
                'AppLabel': app_label,
                'ModelName': model_name,
                'model_name': str(model_name).lower(),
                'module_path': module_path,
                'fields_json': json.dumps(fields, ensure_ascii=False, indent=2),
            }

            # serializers.py 追加/创建
            serializers_py = app_dir / 'serializers.py'
            ser_tpl = 'backend/serializers_enhanced.py.tpl' if enhanced else 'backend/serializers.py.tpl'
            ser_code = load(ser_tpl).safe_substitute(ctx)
            if serializers_py.exists():
                with serializers_py.open('a', encoding='utf-8') as f:
                    f.write('\n\n')
                    f.write(ser_code)
            else:
                serializers_py.write_text(ser_code, encoding='utf-8')

            # views.py 追加/创建（根据 enhanced 选择模板）
            views_py = app_dir / 'views.py'
            tpl_name = 'backend/views_enhanced.py.tpl' if enhanced else 'backend/views.py.tpl'
            view_code = load(tpl_name).safe_substitute(ctx)
            if views_py.exists():
                with views_py.open('a', encoding='utf-8') as f:
                    f.write('\n\n')
                    f.write(view_code)
            else:
                views_py.write_text(view_code, encoding='utf-8')

            # urls.py 注入 router 与 register
            urls_py = app_dir / 'urls.py'
            if urls_py.exists():
                text = urls_py.read_text(encoding='utf-8')
                import re
                # ensure include in django.urls import
                m = re.search(r"^from django\.urls import ([^\n]+)$", text, re.M)
                if m:
                    parts = [p.strip() for p in m.group(1).split(',') if p.strip()]
                    if 'include' not in parts:
                        parts.append('include')
                    new_import = 'from django.urls import ' + ', '.join(sorted(set(parts)))
                    text = text[:m.start()] + new_import + text[m.end():]
                else:
                    if 'from django.urls import path, include' not in text:
                        text = 'from django.urls import path, include\n' + text
                # ensure DefaultRouter import
                if 'DefaultRouter' not in text:
                    text = 'from rest_framework.routers import DefaultRouter\n' + text
                # ensure router
                if 'router = DefaultRouter()' not in text:
                    text += '\n\nrouter = DefaultRouter()\n'
                # ensure register appears AFTER router init and BEFORE urlpatterns block
                register_line = f"router.register(r'{str(model_name).lower()}', {model_name}ViewSet, basename='{str(model_name).lower()}')\n"
                import_line = f'from .views import {model_name}ViewSet\n'
                if import_line not in text:
                    text = import_line + text
                # remove any duplicate existing register lines
                if register_line in text:
                    text = text.replace(register_line, '')
                # insert before urlpatterns (or at end if not found)
                url_pos = text.find('urlpatterns')
                if url_pos == -1:
                    text += register_line
                else:
                    text = text[:url_pos] + register_line + text[url_pos:]
                # normalize urlpatterns: remove stray empty list
                text = re.sub(r"^urlpatterns\s*=\s*\[\s*\]\s*$", '', text, flags=re.M)
                if 'urlpatterns' in text and 'include(router.urls)' in text:
                    pass
                elif 'urlpatterns = router.urls' in text:
                    text = text.replace('urlpatterns = router.urls', 'urlpatterns = [\n    path(\'\', include(router.urls)),\n]')
                else:
                    text += '\nurlpatterns = [\n    path(\'\', include(router.urls)),\n]\n'
                urls_py.write_text(text, encoding='utf-8')
            else:
                urls_code = (
                    'from django.urls import path, include\n'
                    'from rest_framework.routers import DefaultRouter\n'
                    f'from .views import {model_name}ViewSet\n\n'
                    'router = DefaultRouter()\n'
                    f"router.register(r'{str(model_name).lower()}', {model_name}ViewSet, basename='{str(model_name).lower()}')\n\n"
                    'urlpatterns = [\n'
                    "    path('', include(router.urls)),\n"
                    ']\n'
                )
                urls_py.write_text(urls_code, encoding='utf-8')

            # 2.1) 将 app 路由注册到项目 urls.py（/api/<app_label>/）
            project_urls = base_dir / 'django_vue_adminx' / 'urls.py'
            try:
                ptxt = project_urls.read_text(encoding='utf-8')
                include_line = f"path('api/{app_label}/', include('apps.{app_label}.urls')),"
                if include_line not in ptxt:
                    if 'from django.urls import path, re_path, include' not in ptxt:
                        ptxt = ptxt.replace('from django.urls import path, re_path, include', 'from django.urls import path, re_path, include')
                    # insert before closing list of urlpatterns
                    insert_pos = ptxt.find(']')
                    if insert_pos != -1:
                        ptxt = ptxt[:insert_pos] + f"    {include_line}\n" + ptxt[insert_pos:]
                    project_urls.write_text(ptxt, encoding='utf-8')
            except Exception:
                pass

            # 3) 前端文件生成（前端在项目根目录，不在 backend 目录）
            fe_base = project_root / 'front-end' / 'src'
            write_file_safe(fe_base / 'api' / f"{str(model_name).lower()}.js", load('frontend/api.js.tpl').safe_substitute(ctx))
            module_parts = [p for p in module_path.split('/') if p]
            write_file_safe(fe_base / 'views' / Path(*module_parts) / 'index.vue', load('frontend/view.vue.tpl').safe_substitute(ctx))
        except Exception as e:
            return Response({'detail': f'生成文件失败: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 2.2) 创建菜单与 RBAC 权限，并授予超级管理员
        try:
            from apps.rbac.models import Permission, Role, Menu

            # 创建/同步菜单（顶级菜单），component 使用前端模块路径
            menu_title = model_name
            # 菜单路由路径统一为单词（不含斜杠），用模型名小写
            menu_path = str(model_name).lower()
            menu_component = module_path if module_path.endswith('/index') else f"{module_path}/index"
            # 放到 'system' 父菜单下（若不存在则创建）
            parent_menu, _ = Menu.objects.get_or_create(path='system', defaults={
                'title': '系统管理', 'component': '', 'icon': 'Setting', 'parent': None, 'order': 1, 'is_hidden': False
            })

            menu_defaults = {
                "title": menu_title,
                "component": menu_component,
                "icon": "",
                "order": 100,
                "parent": parent_menu,
                "is_hidden": False,
            }
            # 用 path 唯一识别菜单
            menu_obj, _ = Menu.objects.get_or_create(path=menu_path, defaults=menu_defaults)
            # 同步必要字段
            changed = False
            if menu_obj.title != menu_title:
                menu_obj.title = menu_title; changed = True
            if menu_obj.component != menu_component:
                menu_obj.component = menu_component; changed = True
            if menu_obj.parent_id != parent_menu.id:
                menu_obj.parent = parent_menu; changed = True
            if changed:
                menu_obj.save(update_fields=["title", "component", "parent"])

            base = f"/api/{app_label}/{str(model_name).lower()}/"
            perms_spec = [
                {"name": f"{model_name} 列表", "code": f"{str(model_name).lower()}:list", "http_method": "GET", "url_pattern": base},
                {"name": f"{model_name} 创建", "code": f"{str(model_name).lower()}:create", "http_method": "POST", "url_pattern": base},
                {"name": f"{model_name} 更新", "code": f"{str(model_name).lower()}:update", "http_method": "PUT", "url_pattern": base + "*"},
                {"name": f"{model_name} 删除", "code": f"{str(model_name).lower()}:delete", "http_method": "DELETE", "url_pattern": base + "*"},
            ]

            created_perm_ids = []
            for spec in perms_spec:
                p, _ = Permission.objects.get_or_create(
                    code=spec["code"],
                    defaults={
                        "name": spec["name"],
                        "http_method": spec["http_method"],
                        "url_pattern": spec["url_pattern"],
                        "menu": menu_obj,
                        "is_active": True,
                    }
                )
                # sync updates if exists
                changed = False
                if p.name != spec["name"]:
                    p.name = spec["name"]; changed = True
                if p.http_method != spec["http_method"]:
                    p.http_method = spec["http_method"]; changed = True
                if p.url_pattern != spec["url_pattern"]:
                    p.url_pattern = spec["url_pattern"]; changed = True
                if p.menu_id != menu_obj.id:
                    p.menu = menu_obj; changed = True
                if changed:
                    p.save(update_fields=["name", "http_method", "url_pattern", "menu"])
                created_perm_ids.append(p.id)

            # grant to super admin role if exists
            admin_role = None
            for q in [
                Role.objects.filter(code__iexact='ADMIN'),
                Role.objects.filter(code__iexact='SUPER_ADMIN'),
                Role.objects.filter(name__in=['超级管理员','SuperAdmin','Administrator'])
            ]:
                admin_role = q.first()
                if admin_role:
                    break
            if admin_role:
                admin_role.permissions.add(*created_perm_ids)
                admin_role.menus.add(menu_obj)
        except Exception:
            # 权限创建失败不影响主流程
            pass

        return Response({
            'detail': '生成成功',
            'model_file': str(models_py),
            'module_path': module_path,
        })


