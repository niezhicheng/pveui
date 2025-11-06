from django.conf import settings
from django.db import models


class Menu(models.Model):
    """前端路由菜单。用于控制页面级访问权限与导航展示。"""
    title = models.CharField(max_length=64, verbose_name='名称')
    path = models.CharField(max_length=128, blank=True, default='', verbose_name='路由路径')
    component = models.CharField(max_length=128, blank=True, default='', verbose_name='组件路径')
    icon = models.CharField(max_length=64, blank=True, default='', verbose_name='图标')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children', verbose_name='父级')
    is_hidden = models.BooleanField(default=False, verbose_name='是否隐藏')

    class Meta:
        verbose_name = '菜单'
        verbose_name_plural = '菜单'
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['order']),
        ]

    def __str__(self) -> str:
        return self.title


class Permission(models.Model):
    """后端接口级权限。可选挂载到菜单（按钮/操作）。"""
    HTTP_METHOD_CHOICES = (
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
        ('ANY', 'ANY'),
    )

    name = models.CharField(max_length=64, verbose_name='名称')
    code = models.CharField(max_length=64, unique=True, verbose_name='编码')
    http_method = models.CharField(max_length=6, choices=HTTP_METHOD_CHOICES, default='ANY', verbose_name='请求方法')
    url_pattern = models.CharField(max_length=256, verbose_name='URL 匹配')
    menu = models.ForeignKey(Menu, null=True, blank=True, on_delete=models.SET_NULL, related_name='permissions', verbose_name='所属菜单')
    is_active = models.BooleanField(default=True, verbose_name='启用')

    class Meta:
        verbose_name = '权限'
        verbose_name_plural = '权限'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['http_method']),
        ]

    def __str__(self) -> str:
        return f"{self.name}({self.code})"


class Role(models.Model):
    """角色：权限集合。"""
    name = models.CharField(max_length=64, unique=True, verbose_name='名称')
    code = models.CharField(max_length=64, unique=True, verbose_name='编码')
    description = models.CharField(max_length=256, blank=True, default='', verbose_name='描述')
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles', verbose_name='权限')
    menus = models.ManyToManyField(Menu, blank=True, related_name='roles', verbose_name='菜单可见')

    DATA_SCOPE_CHOICES = (
        ('ALL', '全部数据'),
        ('DEPT', '本部门'),
        ('DEPT_AND_SUB', '本部门及下级'),
        ('SELF', '仅本人'),
        ('CUSTOM', '自定义组织'),
    )

    data_scope = models.CharField(max_length=16, choices=DATA_SCOPE_CHOICES, default='SELF', verbose_name='数据范围')

    class Meta:
        verbose_name = '角色'
        verbose_name_plural = '角色'
        indexes = [
            models.Index(fields=['code']),
        ]

    def __str__(self) -> str:
        return self.name


# 将角色关联到用户。使用 settings.AUTH_USER_MODEL 以兼容自定义用户模型
User = settings.AUTH_USER_MODEL


class UserRole(models.Model):
    """用户与角色多对多中间表，便于加元信息和唯一性约束。"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles', verbose_name='用户')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles', verbose_name='角色')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='绑定时间')

    class Meta:
        verbose_name = '用户角色'
        verbose_name_plural = '用户角色'
        unique_together = ('user', 'role')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['role']),
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.role}"


class Organization(models.Model):
    """组织/部门管理，支持树结构。"""
    name = models.CharField(max_length=64, verbose_name='名称')
    code = models.CharField(max_length=64, unique=True, verbose_name='编码')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children', verbose_name='上级组织')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='启用')
    leader = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='lead_organizations', verbose_name='负责人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '组织'
        verbose_name_plural = '组织'
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['order']),
            models.Index(fields=['code']),
        ]

    def __str__(self) -> str:
        return self.name


# 角色在自定义数据范围下可指定可见组织集合
Role.add_to_class('custom_data_organizations', models.ManyToManyField(
    Organization, blank=True, related_name='roles_with_custom_scope', verbose_name='自定义数据范围组织'
))


class UserOrganization(models.Model):
    """用户与组织关联，支持多组织与主组织标记。"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_organizations', verbose_name='用户')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='user_organizations', verbose_name='组织')
    is_primary = models.BooleanField(default=False, verbose_name='是否主组织')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='绑定时间')

    class Meta:
        verbose_name = '用户组织'
        verbose_name_plural = '用户组织'
        unique_together = ('user', 'organization')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['organization']),
            models.Index(fields=['is_primary']),
        ]

    def __str__(self) -> str:
        primary_mark = ' (主)' if self.is_primary else ''
        return f"{self.user} -> {self.organization}{primary_mark}"

