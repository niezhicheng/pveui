"""通用母版序列化器。

特性：
- 动态字段：支持 include_fields / exclude_fields 精细控制输出字段
- 统一字符串清洗：默认 strip 文本字段
- 统一日期时间格式：支持 context 传入 datetime_format（可选）

用法示例（业务模块）：

class ProductSerializer(BaseModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

# 视图中：ProductList 使用更少字段
# ProductDetail 使用完整字段（配合 ActionSerializerMixin，见 viewsets.py）
"""

from typing import Iterable, Optional
from rest_framework import serializers


class BaseModelSerializer(serializers.ModelSerializer):
    """业务通用母版 ModelSerializer。"""

    def __init__(self, *args, **kwargs):
        include_fields: Optional[Iterable[str]] = kwargs.pop('include_fields', None)
        exclude_fields: Optional[Iterable[str]] = kwargs.pop('exclude_fields', None)
        super().__init__(*args, **kwargs)

        # 动态字段裁剪
        if include_fields is not None:
            allowed = set(include_fields)
            for field_name in list(self.fields.keys()):
                if field_name not in allowed:
                    self.fields.pop(field_name)
        if exclude_fields is not None:
            for field_name in exclude_fields:
                self.fields.pop(field_name, None)

    # 统一清洗：去除所有 CharField 文本首尾空白
    def validate(self, attrs):
        for name, field in self.fields.items():
            if name in attrs and isinstance(field, serializers.CharField):
                value = attrs.get(name)
                if isinstance(value, str):
                    attrs[name] = value.strip()
        return super().validate(attrs)

    # 可选统一时间格式输出：context['datetime_format'] = '%Y-%m-%d %H:%M:%S'
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        dt_fmt = self.context.get('datetime_format') if hasattr(self, 'context') else None
        if not dt_fmt:
            return rep
        for key, value in list(rep.items()):
            # 简单处理：ISO 字符串不做解析（避免性能开销），仅处理 datetime 对象场景
            obj = getattr(instance, key, None)
            try:
                # 避免导入 datetime，直接 duck-typing 检测 strftime
                if obj is not None and hasattr(obj, 'strftime'):
                    rep[key] = obj.strftime(dt_fmt)
            except Exception:
                pass
        return rep


