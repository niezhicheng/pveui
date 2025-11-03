"""ViewSet 工具：按动作选择不同序列化器。

用法（业务模块）：

class ProductViewSet(ActionSerializerMixin, ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer  # 兜底
    serializer_action_classes = {
        'list': ProductListSerializer,
        'retrieve': ProductDetailSerializer,
        'create': ProductCreateSerializer,
        'update': ProductUpdateSerializer,
        'partial_update': ProductUpdateSerializer,
    }
"""

from rest_framework import viewsets


class ActionSerializerMixin:
    """根据动作选择不同序列化器的混入类。

    子类只需声明属性即可，无需覆写方法：
      - list_serializer_class
      - retrieve_serializer_class
      - create_serializer_class
      - update_serializer_class
      - partial_update_serializer_class
      - destroy_serializer_class

    兼容旧用法：也可提供 dict serializer_action_classes = { 'list': S1, 'retrieve': S2, ... }

    优先级：
      1) <action>_serializer_class 属性
      2) serializer_action_classes[action]
      3) serializer_class（兜底）
    """

    serializer_action_classes = None  # type: ignore

    # 显式声明以提升可读性（非必需）
    list_serializer_class = None
    retrieve_serializer_class = None
    create_serializer_class = None
    update_serializer_class = None
    partial_update_serializer_class = None
    destroy_serializer_class = None

    def get_serializer_class(self):  # noqa: D401
        action = getattr(self, 'action', None)
        if action:
            # 1) 先查找 <action>_serializer_class 属性
            attr_name = f"{action}_serializer_class"
            specific = getattr(self, attr_name, None)
            if specific is not None:
                return specific

            # 2) 查找映射表
            mapping = getattr(self, 'serializer_action_classes', None) or {}
            if action in mapping:
                return mapping[action]
        # 3) 兜底
        return super().get_serializer_class()
