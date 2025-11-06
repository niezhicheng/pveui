"""任务函数示例"""
import time


def NoParams():
    """无参任务示例"""
    print("执行无参任务")


def Params(*args):
    """有参任务示例"""
    print(f"执行有参任务，参数: {args}")
    now = time.time()
    print("开始执行任务",now)

