"""知识库序列化器。"""

from apps.common.serializers import BaseModelSerializer
from apps.rbac.serializers import OrganizationSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import KnowledgeArticle

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class KnowledgeArticleListSerializer(BaseModelSerializer):
    owner_organization = OrganizationSerializer(read_only=True)
    created_by = SimpleUserSerializer(read_only=True)

    class Meta:
        model = KnowledgeArticle
        fields = [
            'id',
            'title',
            'summary',
            'category',
            'tags',
            'is_published',
            'is_pinned',
            'created_at',
            'updated_at',
            'created_by',
            'owner_organization',
        ]


class KnowledgeArticleDetailSerializer(BaseModelSerializer):
    owner_organization = OrganizationSerializer(read_only=True)
    created_by = SimpleUserSerializer(read_only=True)
    updated_by = SimpleUserSerializer(read_only=True)

    class Meta:
        model = KnowledgeArticle
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class KnowledgeArticleCreateSerializer(BaseModelSerializer):
    class Meta:
        model = KnowledgeArticle
        fields = [
            'title',
            'summary',
            'content',
            'category',
            'tags',
            'is_published',
            'is_pinned',
            'owner_organization',
            'remark',
        ]


class KnowledgeArticleUpdateSerializer(BaseModelSerializer):
    class Meta:
        model = KnowledgeArticle
        fields = [
            'title',
            'summary',
            'content',
            'category',
            'tags',
            'is_published',
            'is_pinned',
            'owner_organization',
            'remark',
        ]


