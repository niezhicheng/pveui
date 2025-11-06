"""初始化 CRUD 示例模块的菜单和权限。

用法：
    python manage.py init_curdexample
    python manage.py init_curdexample --reset  # 删除现有数据后重新创建
"""

from django.core.management.base import BaseCommand
from apps.rbac.models import Menu, Permission, Role


class Command(BaseCommand):
    help = '初始化 CRUD 示例模块的菜单和权限'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='删除现有数据后重新创建（危险操作）',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('正在删除现有 CRUD 示例模块的菜单和权限...'))
            # 删除相关权限
            Permission.objects.filter(code__startswith='example:').delete()
            # 删除菜单（如果存在）
            Menu.objects.filter(path='/system/example').delete()
            self.stdout.write(self.style.SUCCESS('已删除现有数据'))

        # 1. 获取或创建系统管理菜单（父菜单）
        self.stdout.write('查找系统管理菜单...')
        menu_system = Menu.objects.filter(path='/system').first()
        if not menu_system:
            self.stdout.write(self.style.ERROR('  ✗ 未找到系统管理菜单，请先运行 python manage.py init_rbac'))
            return
        self.stdout.write(self.style.SUCCESS(f'  ✓ 找到系统管理菜单: {menu_system.title}'))

        # 2. 创建示例管理菜单
        self.stdout.write('创建示例管理菜单...')
        menu_example = self._get_or_create_menu(
            '示例管理',
            '/system/example',
            'curdexample/index',  # 前端组件路径（需要创建对应的前端页面）
            'FileText',
            menu_system,
            6  # 排序，放在系统管理菜单的最后
        )
        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建菜单: {menu_example.title}'))

        # 3. 创建权限
        self.stdout.write('创建权限...')
        perms = []
        
        # 示例管理权限
        perms.append(self._get_or_create_permission(
            '示例列表',
            'example:list',
            'GET',
            '/api/curd/examples/',
            menu_example
        ))
        perms.append(self._get_or_create_permission(
            '示例详情',
            'example:retrieve',
            'GET',
            '/api/curd/examples/{id}/',
            menu_example
        ))
        perms.append(self._get_or_create_permission(
            '示例创建',
            'example:create',
            'POST',
            '/api/curd/examples/',
            menu_example
        ))
        perms.append(self._get_or_create_permission(
            '示例更新',
            'example:update',
            'PUT',
            '/api/curd/examples/{id}/',
            menu_example
        ))
        perms.append(self._get_or_create_permission(
            '示例部分更新',
            'example:partial_update',
            'PATCH',
            '/api/curd/examples/{id}/',
            menu_example
        ))
        perms.append(self._get_or_create_permission(
            '示例删除',
            'example:delete',
            'DELETE',
            '/api/curd/examples/{id}/',
            menu_example
        ))
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建权限: {len(perms)} 个'))

        # 4. 将权限添加到管理员角色
        self.stdout.write('分配权限到管理员角色...')
        role_admin = Role.objects.filter(code='ADMIN').first()
        if role_admin:
            # 添加新权限到现有权限集合
            existing_perms = set(role_admin.permissions.all())
            existing_perms.update(perms)
            role_admin.permissions.set(existing_perms)
            
            # 添加菜单到现有菜单集合
            existing_menus = set(role_admin.menus.all())
            existing_menus.add(menu_example)
            role_admin.menus.set(existing_menus)
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ 已将权限和菜单添加到角色: {role_admin.name}'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠ 未找到管理员角色，请先运行 python manage.py init_rbac'))

        self.stdout.write(self.style.SUCCESS('\n✅ CRUD 示例模块初始化完成！'))
        self.stdout.write(self.style.SUCCESS('💡 提示：前端需要在 src/views/curdexample/index.vue 创建对应的页面组件'))

    def _get_or_create_menu(self, title, path, component, icon, parent, order):
        """获取或创建菜单。"""
        menu, created = Menu.objects.get_or_create(
            path=path,
            defaults={
                'title': title,
                'component': component,
                'icon': icon,
                'parent': parent,
                'order': order,
                'is_hidden': False,
            }
        )
        if not created:
            menu.title = title
            menu.component = component
            menu.icon = icon
            menu.parent = parent
            menu.order = order
            menu.save()
        return menu

    def _get_or_create_permission(self, name, code, http_method, url_pattern, menu):
        """获取或创建权限。"""
        perm, created = Permission.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'http_method': http_method,
                'url_pattern': url_pattern,
                'menu': menu,
                'is_active': True,
            }
        )
        if not created:
            perm.name = name
            perm.http_method = http_method
            perm.url_pattern = url_pattern
            perm.menu = menu
            perm.save()
        return perm

