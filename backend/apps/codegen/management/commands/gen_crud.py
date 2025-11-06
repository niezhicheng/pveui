import os
import json
import importlib
from pathlib import Path
from string import Template
from typing import Dict, Any, List

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


TEMPLATES_DIR = Path(settings.BASE_DIR) / 'apps' / 'codegen' / 'templates'


def load_template(rel_path: str) -> Template:
    path = TEMPLATES_DIR / rel_path
    if not path.exists():
        raise CommandError(f'Template not found: {path}')
    return Template(path.read_text(encoding='utf-8'))


def write_file_safe(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        # Avoid accidental overwrite: write with .gen suffix
        target = target.with_suffix(target.suffix + '.gen')
    target.write_text(content, encoding='utf-8')


def infer_fields_from_model(model) -> List[Dict[str, Any]]:
    fields = []
    for f in model._meta.get_fields():
        # Skip many-to-one reverse, etc.
        if getattr(f, 'auto_created', False) and not getattr(f, 'concrete', False):
            continue
        if f.many_to_many and f.auto_created:
            continue
        field_type = f.get_internal_type()
        fields.append({
            'name': f.name,
            'type': field_type,
            'null': getattr(f, 'null', False),
            'blank': getattr(f, 'blank', False),
            'primary_key': getattr(f, 'primary_key', False),
            'related': getattr(f, 'related_model', None).__name__ if getattr(f, 'related_model', None) else None,
        })
    return fields


class Command(BaseCommand):
    help = 'Generate CRUD backend/frontend files from a Django model.'

    def add_arguments(self, parser):
        parser.add_argument('app_label', type=str, help='Django app label, e.g., curdexample or rbac')
        parser.add_argument('model_name', type=str, help='Model name, e.g., Example')
        parser.add_argument('--module', type=str, default=None, help='Frontend module path, e.g., system/example')
        parser.add_argument('--out', type=str, default='generated', help='Output subdir for backend files')

    def handle(self, *args, **options):
        app_label = options['app_label']
        model_name = options['model_name']
        module_path = options['module'] or f'{app_label}/{model_name.lower()}'
        out_dir = options['out']

        try:
            models_mod = importlib.import_module(f'apps.{app_label}.models')
            model = getattr(models_mod, model_name)
        except Exception as e:
            raise CommandError(f'Load model failed: {e}')

        fields = infer_fields_from_model(model)

        ctx = {
            'AppLabel': app_label,
            'ModelName': model_name,
            'model_name': model_name.lower(),
            'module_path': module_path,
            'fields_json': json.dumps(fields, ensure_ascii=False, indent=2),
        }

        # Backend files
        serializers_tpl = load_template('backend/serializers.py.tpl')
        views_tpl = load_template('backend/views.py.tpl')
        urls_tpl = load_template('backend/urls.py.tpl')

        backend_base = Path(settings.BASE_DIR) / 'apps' / app_label / out_dir / model_name.lower()
        write_file_safe(backend_base / f'serializers_{model_name.lower()}.py', serializers_tpl.safe_substitute(ctx))
        write_file_safe(backend_base / f'views_{model_name.lower()}.py', views_tpl.safe_substitute(ctx))
        write_file_safe(backend_base / f'urls_{model_name.lower()}.py', urls_tpl.safe_substitute(ctx))

        # Frontend files
        fe_api_tpl = load_template('frontend/api.js.tpl')
        fe_view_tpl = load_template('frontend/view.vue.tpl')

        fe_base = Path(settings.BASE_DIR) / 'front-end' / 'src'
        write_file_safe(fe_base / 'api' / f"{model_name.lower()}.js", fe_api_tpl.safe_substitute(ctx))
        # put under views/<app_label>/<model>/index.vue
        module_parts = module_path.split('/')
        view_dir = fe_base / 'views' / Path(*module_parts)
        write_file_safe(view_dir / 'index.vue', fe_view_tpl.safe_substitute(ctx))

        self.stdout.write(self.style.SUCCESS('CRUD code generated successfully.'))
        self.stdout.write(f"Backend out: {backend_base}")
        self.stdout.write(f"Frontend api: {fe_base / 'api' / f'{model_name.lower()}.js'}")
        self.stdout.write(f"Frontend view: {view_dir / 'index.vue'}")

