from rest_framework import serializers
from apps.${AppLabel}.models import ${ModelName}


class ${ModelName}Serializer(serializers.ModelSerializer):
    class Meta:
        model = ${ModelName}
        fields = '__all__'

