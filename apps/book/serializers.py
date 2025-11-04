from rest_framework import serializers
from apps.book.models import Book


class BookListSerializer(serializers.ModelSerializer):
    """列表场景序列化器

    适合列表页展示；可按需裁剪字段、添加只读字段。
    """

    class Meta:
        model = Book
        fields = '__all__'


class BookDetailSerializer(serializers.ModelSerializer):
    """详情/检索场景序列化器

    用于 retrieve 场景；可展开外键/嵌套子对象。
    """

    class Meta:
        model = Book
        fields = '__all__'


class BookCreateSerializer(serializers.ModelSerializer):
    """创建场景序列化器

    可定义必填/默认值/校验规则；审计与归属由 Mixin 自动填充。
    """

    class Meta:
        model = Book
        fields = '__all__'


class BookUpdateSerializer(serializers.ModelSerializer):
    """更新场景序列化器

    可限制不可更改字段；审计字段由 Mixin 自动维护。
    """

    class Meta:
        model = Book
        fields = '__all__'


