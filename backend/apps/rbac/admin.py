from django.contrib import admin
from .models import Menu, Permission, Role, UserRole, Organization, UserOrganization

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'path', 'component', 'parent', 'order', 'is_hidden')
    list_filter = ('is_hidden',)
    search_fields = ('title', 'path', 'component')
    ordering = ('order', 'id')


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'http_method', 'url_pattern', 'menu', 'is_active')
    list_filter = ('http_method', 'is_active')
    search_fields = ('name', 'code', 'url_pattern')
    ordering = ('id',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'description', 'data_scope')
    list_filter = ('data_scope',)
    search_fields = ('name', 'code')
    filter_horizontal = ('permissions', 'menus', 'custom_data_organizations')


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'role', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'role__name')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'parent', 'order', 'is_active', 'leader')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('order', 'id')


@admin.register(UserOrganization)
class UserOrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'organization', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'organization')
    search_fields = ('user__username', 'organization__name')
