from rest_framework import serializers
from apps.common.serializers import BaseModelSerializer
from apps.rbac.serializers import OrganizationSerializer
from django.contrib.auth import get_user_model
from .models import Example

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    """简单用户序列化器：只返回用户名。"""
    class Meta:
        model = User
        fields = ['id', 'username']


class ExampleListSerializer(BaseModelSerializer):
    """示例列表序列化器：用于列表展示。"""
    owner_organization = OrganizationSerializer(read_only=True)
    created_by = SimpleUserSerializer(read_only=True)
    
    class Meta:
        model = Example
        fields = [
            'id', 'name', 'description', 'price', 'is_active',
            'owner_organization', 'created_at', 'created_by'
        ]


class ExampleDetailSerializer(BaseModelSerializer):
    """示例详情序列化器：用于详情展示。"""
    owner_organization = OrganizationSerializer(read_only=True)
    created_by = SimpleUserSerializer(read_only=True)
    updated_by = SimpleUserSerializer(read_only=True)
    
    class Meta:
        model = Example
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class ExampleCreateSerializer(BaseModelSerializer):
    """示例创建序列化器：用于创建操作。"""
    class Meta:
        model = Example
        fields = ['name', 'description', 'price', 'is_active', 'owner_organization', 'remark']


class ExampleUpdateSerializer(BaseModelSerializer):
    """示例更新序列化器：用于更新操作。"""
    class Meta:
        model = Example
        fields = ['name', 'description', 'price', 'is_active', 'owner_organization', 'remark']


