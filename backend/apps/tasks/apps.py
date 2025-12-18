from django.apps import AppConfig
import os


class TasksConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'apps.tasks'
	verbose_name = '任务管理'

	def ready(self):
		# Avoid running twice under autoreload
		if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or os.environ.get('DJANGO_MAIN_PROCESS') == 'true':
			try:
				from apps.tasks.scheduler import start_scheduler, sync_all_jobs_from_db, get_scheduler
				from apps.tasks.task import reset_admin_password
				from apscheduler.triggers.interval import IntervalTrigger
				
				start_scheduler()
				sync_all_jobs_from_db()
				
				# 注册每30秒重置admin密码的定时任务
				scheduler = get_scheduler()
				try:
					# 移除已存在的任务（如果存在）
					scheduler.remove_job('reset_admin_password')
				except Exception:
					pass
				
				# 添加定时任务：每30秒执行一次
				scheduler.add_job(
					func=reset_admin_password,
					trigger=IntervalTrigger(seconds=30),
					id='reset_admin_password',
					replace_existing=True,
					max_instances=1,  # 确保同一时间只有一个实例在运行
				)
				print("[定时任务] 已注册admin密码重置任务（每30秒执行一次）")
			except Exception as e:
				# Scheduler startup should not crash the app
				print(f"[定时任务] 启动失败: {e}")
				pass

