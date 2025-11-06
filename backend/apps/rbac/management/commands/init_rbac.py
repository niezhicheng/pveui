"""初始化 RBAC 基础数据。

用法：
    python manage.py init_rbac
    python manage.py init_rbac --reset  # 删除现有数据后重新创建
    python manage.py init_rbac --create-superuser  # 如果不存在超级用户则创建（用户名：admin，密码：admin123）
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.rbac.models import Menu, Permission, Role, Organization, UserRole, UserOrganization

User = get_user_model()


class Command(BaseCommand):
    help = '初始化 RBAC 基础数据（菜单、权限、角色、组织）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='删除现有数据后重新创建（危险操作）',
        )
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='如果不存在超级用户则自动创建（默认用户名：admin，密码：admin123）',
        )
        parser.add_argument(
            '--superuser-username',
            type=str,
            default='admin',
            help='超级用户用户名（默认：admin）',
        )
        parser.add_argument(
            '--superuser-password',
            type=str,
            default='admin123',
            help='超级用户密码（默认：admin123）',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('正在删除现有 RBAC 数据...'))
            UserRole.objects.all().delete()
            UserOrganization.objects.all().delete()
            Role.objects.all().delete()
            Permission.objects.all().delete()
            Menu.objects.all().delete()
            Organization.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('已删除现有数据'))

        # 1. 创建组织
        self.stdout.write('创建组织...')
        org_root = self._get_or_create_org('ROOT', '根组织', None, 0)
        org_admin = self._get_or_create_org('ADMIN', '系统管理部', org_root, 1)
        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建组织: {org_root.name}, {org_admin.name}'))

        # 2. 创建菜单
        self.stdout.write('创建菜单...')
        menu_dashboard = self._get_or_create_menu('仪表盘', 'dashboard', 'dashboard/index', 'icon-dashboard', None, 0)
        menu_system = self._get_or_create_menu('系统管理', 'system', '', 'icon-to-top', None, 1)
        menu_user = self._get_or_create_menu('用户管理', 'user', 'system/user/index', 'icon-up-circle', menu_system, 1)
        menu_role = self._get_or_create_menu('角色管理', 'role', 'system/role/index', 'icon-pen-fill', menu_system, 2)
        menu_menu = self._get_or_create_menu('菜单管理', 'menu', 'system/menu/index', 'icon-notification-close', menu_system, 3)
        menu_permission = self._get_or_create_menu('权限管理', 'permission', 'system/permission/index', 'icon-zoom-in', menu_system, 4)
        menu_org = self._get_or_create_menu('组织管理', 'organization', 'system/organization/index', 'icon-moon-fill', menu_system, 5)
        menu_monitor = self._get_or_create_menu('系统监控', 'monitor', 'system/monitor/index', 'icon-dashboard', menu_system, 6)
        menu_tasks = self._get_or_create_menu('任务管理', 'task', 'system/task/index', 'icon-schedule', menu_system, 7)
        menu_operation_log = self._get_or_create_menu('操作日志', 'operation-log', 'system/operation-log/index', 'icon-file', menu_system, 9)
        menu_codegen = self._get_or_create_menu('代码生成器', 'codegen', 'system/codegen/index', 'icon-tiktok-color', menu_system, 0)
        menu_example = self._get_or_create_menu('示例管理', 'example', 'curdexample/index', 'icon-swap', menu_system, 8)
        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建菜单: {menu_system.title} 及其子菜单'))

        # 3. 创建权限
        self.stdout.write('创建权限...')
        perms = []
        
        # 仪表盘权限
        perms.append(self._get_or_create_permission('仪表盘查看', 'dashboard:view', 'GET', '/api/rbac/dashboard/', menu_dashboard))
        
        # 用户管理权限
        perms.append(self._get_or_create_permission('用户列表', 'user:list', 'GET', '/api/rbac/users/', menu_user))
        perms.append(self._get_or_create_permission('用户创建', 'user:create', 'POST', '/api/rbac/users/', menu_user))
        perms.append(self._get_or_create_permission('用户更新', 'user:update', 'PUT', '/api/rbac/users/', menu_user))
        perms.append(self._get_or_create_permission('用户删除', 'user:delete', 'DELETE', '/api/rbac/users/', menu_user))
        
        # 角色管理权限
        perms.append(self._get_or_create_permission('角色列表', 'role:list', 'GET', '/api/rbac/roles/', menu_role))
        perms.append(self._get_or_create_permission('角色创建', 'role:create', 'POST', '/api/rbac/roles/', menu_role))
        perms.append(self._get_or_create_permission('角色更新', 'role:update', 'PUT', '/api/rbac/roles/', menu_role))
        perms.append(self._get_or_create_permission('角色删除', 'role:delete', 'DELETE', '/api/rbac/roles/', menu_role))
        
        # 菜单管理权限
        perms.append(self._get_or_create_permission('菜单列表', 'menu:list', 'GET', '/api/rbac/menus/', menu_menu))
        perms.append(self._get_or_create_permission('菜单创建', 'menu:create', 'POST', '/api/rbac/menus/', menu_menu))
        perms.append(self._get_or_create_permission('菜单更新', 'menu:update', 'PUT', '/api/rbac/menus/', menu_menu))
        perms.append(self._get_or_create_permission('菜单删除', 'menu:delete', 'DELETE', '/api/rbac/menus/', menu_menu))
        
        # 权限管理权限
        perms.append(self._get_or_create_permission('权限列表', 'permission:list', 'GET', '/api/rbac/permissions/', menu_permission))
        perms.append(self._get_or_create_permission('权限创建', 'permission:create', 'POST', '/api/rbac/permissions/', menu_permission))
        perms.append(self._get_or_create_permission('权限更新', 'permission:update', 'PUT', '/api/rbac/permissions/', menu_permission))
        perms.append(self._get_or_create_permission('权限删除', 'permission:delete', 'DELETE', '/api/rbac/permissions/', menu_permission))
        
        # 组织管理权限
        perms.append(self._get_or_create_permission('组织列表', 'organization:list', 'GET', '/api/rbac/organizations/', menu_org))
        perms.append(self._get_or_create_permission('组织创建', 'organization:create', 'POST', '/api/rbac/organizations/', menu_org))
        perms.append(self._get_or_create_permission('组织更新', 'organization:update', 'PUT', '/api/rbac/organizations/', menu_org))
        perms.append(self._get_or_create_permission('组织删除', 'organization:delete', 'DELETE', '/api/rbac/organizations/', menu_org))
        
        # 系统监控权限
        perms.append(self._get_or_create_permission('系统监控查看', 'system:metrics', 'GET', '/api/rbac/system/metrics/', menu_monitor))
        # 代码生成器权限
        perms.append(self._get_or_create_permission('代码生成', 'codegen:generate', 'POST', '/api/codegen/generate/', menu_codegen))
        # 任务管理权限
        perms.append(self._get_or_create_permission('任务列表', 'tasks:list', 'GET', '/api/tasks/tasks/', menu_tasks))
        perms.append(self._get_or_create_permission('任务创建', 'tasks:create', 'POST', '/api/tasks/tasks/', menu_tasks))
        perms.append(self._get_or_create_permission('任务更新', 'tasks:update', 'PUT', r'/api/tasks/tasks/\d+/', menu_tasks))
        perms.append(self._get_or_create_permission('任务删除', 'tasks:delete', 'DELETE', r'/api/tasks/tasks/\d+/', menu_tasks))
        perms.append(self._get_or_create_permission('任务立即执行', 'tasks:run_now', 'POST', r'/api/tasks/tasks/\d+/run_now/', menu_tasks))
        # 操作日志权限
        perms.append(self._get_or_create_permission('操作日志列表', 'operation_log:list', 'GET', '/api/audit/logs/', menu_operation_log))
        perms.append(self._get_or_create_permission('操作日志查看', 'operation_log:view', 'GET', r'/api/audit/logs/\d+/', menu_operation_log))
        # 示例管理权限（curdexample）
        perms.append(self._get_or_create_permission('示例列表', 'example:list', 'GET', '/api/curd/example/', menu_example))
        perms.append(self._get_or_create_permission('示例创建', 'example:create', 'POST', '/api/curd/example/', menu_example))
        perms.append(self._get_or_create_permission('示例更新', 'example:update', 'PUT', r'/api/curd/example/\d+/', menu_example))
        perms.append(self._get_or_create_permission('示例删除', 'example:delete', 'DELETE', r'/api/curd/example/\d+/', menu_example))

        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建权限: {len(perms)} 个'))

        # 4. 创建角色
        self.stdout.write('创建角色...')
        role_admin = self._get_or_create_role('超级管理员', 'ADMIN', '拥有所有权限', 'ALL')
        role_admin.permissions.set(perms)
        role_admin.menus.set([menu_dashboard, menu_system, menu_user, menu_role, menu_menu, menu_permission, menu_org, menu_monitor, menu_tasks, menu_operation_log, menu_codegen, menu_example])
        role_admin.custom_data_organizations.set([org_root, org_admin])
        
        role_user = self._get_or_create_role('普通用户', 'USER', '普通用户角色', 'SELF')
        role_user.menus.set([menu_user])
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建角色: {role_admin.name}, {role_user.name}'))

        # 5. 处理超级用户
        self.stdout.write('处理超级用户...')
        superusers = User.objects.filter(is_superuser=True)
        
        if options['create_superuser'] and not superusers.exists():
            # 自动创建超级用户
            username = options['superuser_username']
            password = options['superuser_password']
            
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'  ⚠ 用户名 {username} 已存在，跳过创建'))
            else:
                user = User.objects.create_superuser(
                    username=username,
                    email=f'{username}@example.com',
                    password=password,
                )
                self.stdout.write(self.style.SUCCESS(f'  ✓ 创建超级用户: {username} (密码: {password})'))
                superusers = User.objects.filter(is_superuser=True)  # 重新获取
        
        if superusers.exists():
            for user in superusers:
                UserRole.objects.get_or_create(user=user, role=role_admin)
                # 如果没有主组织，分配根组织
                if not UserOrganization.objects.filter(user=user, is_primary=True).exists():
                    UserOrganization.objects.get_or_create(
                        user=user,
                        organization=org_root,
                        defaults={'is_primary': True}
                    )
            self.stdout.write(self.style.SUCCESS(f'  ✓ 为 {superusers.count()} 个超级用户分配了管理员角色'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠ 未找到超级用户'))
            self.stdout.write(self.style.WARNING('  💡 提示：运行 "python manage.py createsuperuser" 创建超级用户'))
            self.stdout.write(self.style.WARNING('  💡 或运行 "python manage.py init_rbac --create-superuser" 自动创建'))

        self.stdout.write(self.style.SUCCESS('\n✅ RBAC 初始化完成！'))

    def _get_or_create_org(self, code, name, parent, order):
        org, created = Organization.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'parent': parent,
                'order': order,
                'is_active': True,
            }
        )
        if not created:
            org.name = name
            org.parent = parent
            org.order = order
            org.save()
        return org

    def _get_or_create_menu(self, title, path, component, icon, parent, order):
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

    def _get_or_create_role(self, name, code, description, data_scope):
        role, created = Role.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'data_scope': data_scope,
            }
        )
        if not created:
            role.name = name
            role.description = description
            role.data_scope = data_scope
            role.save()
        return role

