from django.db import models
from apps.common.models import BaseAuditModel


class Job(BaseAuditModel):
    """定时任务模型 - 简化版"""
    
    job_name = models.CharField(max_length=100, unique=True, verbose_name='任务名称')
    invoke_target = models.CharField(max_length=255, verbose_name='调用目标')  # 如: NoParams, Params
    job_params = models.JSONField(default=list, blank=True, verbose_name='参数')
    cron_expression = models.CharField(max_length=100, default='* * * * *', verbose_name='Cron表达式')
    next_valid_time = models.DateTimeField(null=True, blank=True, verbose_name='下次执行时间')
    status = models.IntegerField(default=1, choices=[(0, '停用'), (1, '启用')], verbose_name='状态')
    job_id = models.CharField(max_length=128, blank=True, default='', editable=False, verbose_name='调度器任务ID')
    last_run_at = models.DateTimeField(null=True, blank=True, editable=False, verbose_name='最后执行时间')
    
    class Meta:
        verbose_name = '定时任务'
        verbose_name_plural = '定时任务'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.job_name
    
    @property
    def enabled(self):
        """兼容属性：status=1表示启用"""
        return self.status == 1
