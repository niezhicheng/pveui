from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import SoftDeleteMixin, AuditOwnerPopulateMixin
from apps.common.data_mixins import DataScopeFilterMixin

from apps.tasks.models import Job
from apps.tasks.serializers import JobSerializer
from apps.tasks.scheduler import add_or_update_job, remove_job, run_job_now


class JobViewSet(DataScopeFilterMixin, AuditOwnerPopulateMixin, SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    filterset_fields = ['status', 'job_name']
    
    def perform_create(self, serializer):
        instance = serializer.save()
        add_or_update_job(instance)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        add_or_update_job(instance)
    
    def perform_destroy(self, instance):
        remove_job(instance)
        return super().perform_destroy(instance)
    
    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """立即执行任务"""
        job = self.get_object()
        try:
            run_job_now(job)
            return Response({'detail': '任务已触发执行'}, status=status.HTTP_200_OK)
        except Exception as exc:  # noqa: BLE001
            return Response({'detail': f'执行失败: {exc}'}, status=status.HTTP_400_BAD_REQUEST)
