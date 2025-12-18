"""任务函数示例"""
import time
from django.contrib.auth import get_user_model

User = get_user_model()


def NoParams():
    """无参任务示例"""
    print("执行无参任务")


def Params(*args):
    """有参任务示例"""
    print(f"执行有参任务，参数: {args}")
    now = time.time()
    print("开始执行任务",now)


def reset_admin_password():
    """重置admin用户密码为admin123"""
    try:
        user = User.objects.get(username='admin')
        user.set_password('admin123')
        user.save()
        print(f"[定时任务] admin密码已重置为admin123 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    except User.DoesNotExist:
        print(f"[定时任务] admin用户不存在 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"[定时任务] 重置admin密码失败: {e} - {time.strftime('%Y-%m-%d %H:%M:%S')}")

