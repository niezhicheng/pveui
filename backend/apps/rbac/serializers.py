"""RBAC 模块的序列化器。

提供 Menu/Permission/Role/UserRole/Organization/UserOrganization 的基础序列化，
默认使用主键写入多对多字段，便于前端直接传递 ID 列表。
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Menu, Permission, Role, UserRole, Organization, UserOrganization

User = get_user_model()


class MenuSerializer(serializers.ModelSerializer):
    """菜单序列化器：提供菜单树基础字段序列化。"""
    class Meta:
        model = Menu
        fields = '__all__'


class PermissionSerializer(serializers.ModelSerializer):
    """权限序列化器：用于接口级权限管理。"""
    class Meta:
        model = Permission
        fields = '__all__'


class RoleSerializer(serializers.ModelSerializer):
    """角色序列化器：包含权限、菜单以及自定义数据范围组织的主键写入。"""
    permissions = serializers.PrimaryKeyRelatedField(many=True, queryset=Permission.objects.all(), required=False)
    menus = serializers.PrimaryKeyRelatedField(many=True, queryset=Menu.objects.all(), required=False)
    custom_data_organizations = serializers.PrimaryKeyRelatedField(many=True, queryset=Organization.objects.all(), required=False)

    class Meta:
        model = Role
        fields = '__all__'


class UserRoleSerializer(serializers.ModelSerializer):
    """用户-角色绑定序列化器：支持批量绑定的基础单条模型。"""
    class Meta:
        model = UserRole
        fields = '__all__'


class OrganizationSerializer(serializers.ModelSerializer):
    """组织序列化器：用于组织树维护与负责人指派。"""
    class Meta:
        model = Organization
        fields = '__all__'


class UserOrganizationSerializer(serializers.ModelSerializer):
    """用户-组织绑定序列化器：支持主组织标记。"""
    class Meta:
        model = UserOrganization
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器：用于用户管理。"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login']
        read_only_fields = ['date_joined', 'last_login']


class UserCreateSerializer(serializers.ModelSerializer):
    """用户创建序列化器：包含密码字段。"""
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """用户更新序列化器：密码可选。"""
    password = serializers.CharField(write_only=True, required=False, min_length=6, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


