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
                # best-effort: dump json for primitive
                args.append(f"default={json.dumps(default, ensure_ascii=False)}")
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

        if not app_label or not model_name:
            return Response({'detail': 'app_label 与 model_name 必填'}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(fields, list) or not fields:
            return Response({'detail': 'fields 需为非空数组'}, status=status.HTTP_400_BAD_REQUEST)

        base_dir = Path(settings.BASE_DIR)
        app_dir = base_dir / 'apps' / app_label
        if not app_dir.exists():
            return Response({'detail': f'app 不存在: {app_label}'}, status=status.HTTP_400_BAD_REQUEST)

        # 1) 生成模型代码片段（安全写入 .gen 文件）
        model_code = build_model_code(app_label, model_name, fields)
        models_out = app_dir / 'generated_models' / f"models_{slugify(model_name)}.py"
        models_written = write_file_safe(models_out, model_code)

        # 2) 生成前后端 CRUD 文件（基于前期模板），不依赖模型已安装
        #    直接用字段 JSON 上下文渲染模板，写入 .gen 文件
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

            # backend
            backend_base = app_dir / 'generated' / str(model_name).lower()
            write_file_safe(backend_base / f'serializers_{str(model_name).lower()}.py', load('backend/serializers.py.tpl').safe_substitute(ctx))
            write_file_safe(backend_base / f'views_{str(model_name).lower()}.py', load('backend/views.py.tpl').safe_substitute(ctx))
            write_file_safe(backend_base / f'urls_{str(model_name).lower()}.py', load('backend/urls.py.tpl').safe_substitute(ctx))

            # frontend
            fe_base = base_dir / 'front-end' / 'src'
            write_file_safe(fe_base / 'api' / f"{str(model_name).lower()}.js", load('frontend/api.js.tpl').safe_substitute(ctx))
            module_parts = [p for p in module_path.split('/') if p]
            write_file_safe(fe_base / 'views' / Path(*module_parts) / 'index.vue', load('frontend/view.vue.tpl').safe_substitute(ctx))
        except Exception as e:
            return Response({'detail': f'生成文件失败: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'detail': '生成成功',
            'model_file': str(models_written),
            'module_path': module_path,
        })


