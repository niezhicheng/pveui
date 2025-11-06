from rest_framework import serializers
from apps.tasks.models import Job


class JobSerializer(serializers.ModelSerializer):
    """任务序列化器 - 对齐前端格式"""
    
    # 字段别名映射
    jobId = serializers.IntegerField(source='id', read_only=True)
    jobName = serializers.CharField(source='job_name')
    invokeTarget = serializers.CharField(source='invoke_target')
    jobParams = serializers.JSONField(source='job_params', default=list)
    cronExpression = serializers.CharField(source='cron_expression')
    nextValidTime = serializers.DateTimeField(source='next_valid_time', read_only=True, allow_null=True)
    status = serializers.IntegerField()
    createBy = serializers.IntegerField(source='created_by_id', read_only=True, allow_null=True)
    createTime = serializers.DateTimeField(source='created_at', read_only=True)
    updateBy = serializers.IntegerField(source='updated_by_id', read_only=True, allow_null=True)
    updateTime = serializers.DateTimeField(source='updated_at', read_only=True, allow_null=True)
    
    class Meta:
        model = Job
        fields = [
            'jobId', 'jobName', 'invokeTarget', 'jobParams', 'cronExpression',
            'nextValidTime', 'status', 'createBy', 'createTime', 'updateBy', 'updateTime'
        ]
    
    def validate_cronExpression(self, value):
        """验证cron表达式格式"""
        parts = value.strip().split()
        if len(parts) not in [5, 6]:
            raise serializers.ValidationError('Cron表达式应为5位（分 时 日 月 周）或6位（秒 分 时 日 月 周）')
        return value
