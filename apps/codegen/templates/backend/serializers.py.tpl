from rest_framework import serializers
from apps.${AppLabel}.models import ${ModelName}


class ${ModelName}Serializer(serializers.ModelSerializer):
    """基础序列化器

    用于简单 CRUD 场景，直接暴露所有字段。
    可根据业务需要将 '__all__' 改为显式字段列表，或新增只读/校验逻辑。
    """

    class Meta:
        model = ${ModelName}
        fields = '__all__'

