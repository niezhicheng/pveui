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
				from apps.tasks.scheduler import start_scheduler, sync_all_jobs_from_db
				start_scheduler()
				sync_all_jobs_from_db()
			except Exception:
				# Scheduler startup should not crash the app
				pass

