"""PVE模块视图集。"""

import json
import logging
import secrets
import mimetypes
from pathlib import Path
from urllib.parse import quote_plus
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import transaction

from apps.common.viewsets import ActionSerializerMixin
from apps.common.mixins import AuditOwnerPopulateMixin
from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponseNotFound, FileResponse, Http404
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.utils._os import safe_join
from django.urls import reverse

from .models import PVEServer, VirtualMachine, NetworkTopology, LXCContainer
from .serializers import (
    PVEServerListSerializer,
    PVEServerDetailSerializer,
    PVEServerCreateSerializer,
    PVEServerUpdateSerializer,
    PVEServerTestSerializer,
    VirtualMachineListSerializer,
    VirtualMachineDetailSerializer,
    VirtualMachineCreateSerializer,
    VirtualMachineActionSerializer,
    VirtualMachineHardwareUpdateSerializer,
    VMOptionsUpdateSerializer,
    VMBackupCreateSerializer,
    VMSnapshotCreateSerializer,
    VMSnapshotActionSerializer,
    VMCloneSerializer,
    NetworkTopologyListSerializer,
    NetworkTopologyDetailSerializer,
    NetworkTopologySaveSerializer,
    LXCContainerListSerializer,
    LXCContainerDetailSerializer,
    LXCContainerActionSerializer,
)
from .pve_client import PVEAPIClient
from .consumers import SESSION_CACHE_PREFIX

logger = logging.getLogger(__name__)
PVE_CONSOLE_SESSION_TTL = getattr(settings, 'PVE_CONSOLE_SESSION_TTL', 60)
NOVNC_ASSETS_DIR = Path(__file__).resolve().parents[2] / 'templates' / 'novnc-pve'


class PVEServerViewSet(AuditOwnerPopulateMixin, ActionSerializerMixin, viewsets.ModelViewSet):
    """PVE服务器CRUD视图集。"""
    
    queryset = PVEServer.objects.all().order_by('name')
    
    serializer_class = PVEServerDetailSerializer
    list_serializer_class = PVEServerListSerializer
    retrieve_serializer_class = PVEServerDetailSerializer
    create_serializer_class = PVEServerCreateSerializer
    update_serializer_class = PVEServerUpdateSerializer
    partial_update_serializer_class = PVEServerUpdateSerializer
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'host']
    ordering_fields = ['id', 'name', 'created_at']
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试PVE服务器连接。"""
        server = self.get_object()
        
        try:
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            # 尝试获取版本信息
            version = client.get_version()
            
            return Response({
                'success': True,
                'message': '连接成功',
                'version': version
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'连接失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def nodes(self, request, pk=None):
        """获取PVE服务器节点列表。"""
        server = self.get_object()
        
        try:
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            nodes = client.get_nodes()
            return Response(nodes)
        except Exception as e:
            return Response({
                'detail': f'获取节点列表失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='nodes/(?P<node>[^/.]+)/vms')
    def node_vms(self, request, pk=None, node=None):
        """获取节点上的虚拟机列表。"""
        server = self.get_object()
        
        try:
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            vms = client.get_vms(node)
            return Response(vms)
        except Exception as e:
            return Response({
                'detail': f'获取虚拟机列表失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='nodes/(?P<node>[^/.]+)/storage')
    def node_storage(self, request, pk=None, node=None):
        """获取节点存储列表。"""
        server = self.get_object()
        
        try:
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            storage = client.get_storage(node)
            return Response(storage)
        except Exception as e:
            return Response({
                'detail': f'获取存储列表失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='nodes/(?P<node>[^/.]+)/storage/(?P<storage>[^/.]+)/content')
    def node_storage_content(self, request, pk=None, node=None, storage=None):
        """获取存储中的内容列表，可按类型过滤。"""
        server = self.get_object()
        content_type = request.query_params.get('content')
        if content_type and content_type.lower() in ('all', 'none'):
            content_type = None
        
        try:
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            content = client.get_storage_content(node, storage, content_type=content_type)
            return Response(content)
        except Exception as e:
            return Response({
                'detail': f'获取存储内容失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='nodes/(?P<node>[^/.]+)/storage/(?P<storage>[^/.]+)/iso')
    def node_storage_iso(self, request, pk=None, node=None, storage=None):
        """获取存储中的ISO镜像列表（兼容旧接口）。"""
        server = self.get_object()
        
        try:
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            content = client.get_storage_content(node, storage, content_type='iso')
            iso_files = [item for item in content if item.get('content') == 'iso']
            return Response(iso_files)
        except Exception as e:
            return Response({
                'detail': f'获取ISO镜像列表失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='nodes/(?P<node>[^/.]+)/storage/(?P<storage>[^/.]+)/upload')
    def node_storage_upload(self, request, pk=None, node=None, storage=None):
        """上传文件到指定存储。"""
        server = self.get_object()
        upload_file = request.FILES.get('file')
        if not upload_file:
            return Response({'detail': '请上传文件'}, status=status.HTTP_400_BAD_REQUEST)
        filename = request.data.get('filename') or upload_file.name
        content_type = request.data.get('content', 'iso')
        
        try:
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            result = client.upload_storage_content(node, storage, upload_file, filename, content=content_type or 'iso')
            return Response({
                'success': True,
                'message': '文件上传成功',
                'result': result
            })
        except Exception as e:
            return Response({
                'detail': f'上传失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='nodes/(?P<node>[^/.]+)/network')
    def node_network(self, request, pk=None, node=None):
        """获取节点网络接口列表。"""
        server = self.get_object()
        
        try:
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            network = client.get_network(node)
            return Response(network)
        except Exception as e:
            return Response({
                'detail': f'获取网络接口失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='global-tasks')
    def global_tasks(self, request):
        """获取所有PVE服务器上的全局任务列表。"""
        from .models import PVEServer
        
        server_id = request.query_params.get('server_id')
        node = request.query_params.get('node')
        statusfilter = request.query_params.get('statusfilter', 'all')
        limit = int(request.query_params.get('limit', 100))
        
        all_tasks = []
        
        # 获取服务器列表
        if server_id:
            servers = PVEServer.objects.filter(id=server_id, is_active=True)
        else:
            servers = PVEServer.objects.filter(is_active=True)
        
        for server in servers:
            try:
                client = PVEAPIClient(
                    host=server.host,
                    port=server.port,
                    token_id=server.token_id,
                    token_secret=server.token_secret,
                    verify_ssl=server.verify_ssl
                )
                
                # 获取节点列表
                nodes_data = client.get_nodes()
                nodes_list = nodes_data if isinstance(nodes_data, list) else [nodes_data] if nodes_data else []
                
                for node_info in nodes_list:
                    node_name = node_info.get('node') or node_info.get('name', '')
                    if node and node != node_name:
                        continue
                    
                    try:
                        tasks = client.list_tasks(
                            node_name,
                            limit=limit,
                            statusfilter=statusfilter if statusfilter != 'all' else None
                        )
                        
                        for task in tasks:
                            task['server_id'] = server.id
                            task['server_name'] = server.name
                            task['server_host'] = server.host
                            task['node'] = node_name
                            all_tasks.append(task)
                    except Exception as e:
                        logger.warning(f'获取节点 {node_name} 任务失败: {str(e)}')
                        continue
                        
            except Exception as e:
                logger.warning(f'获取服务器 {server.name} 任务失败: {str(e)}')
                continue
        
        # 按开始时间倒序排序
        all_tasks.sort(key=lambda x: x.get('starttime', 0) or 0, reverse=True)
        
        return Response({
            'tasks': all_tasks[:limit],
            'total': len(all_tasks)
        })
    
    @action(detail=False, methods=['post'], url_path='task-log')
    def global_task_log(self, request):
        """获取全局任务日志。"""
        server_id = request.data.get('server_id')
        node = request.data.get('node')
        upid = request.data.get('upid')
        
        if not server_id or not node or not upid:
            return Response({
                'detail': '缺少必要参数: server_id, node, upid'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .models import PVEServer
            server = PVEServer.objects.get(id=server_id, is_active=True)
            
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            start = int(request.data.get('start', 0))
            limit = int(request.data.get('limit', 200))
            log_lines = client.get_task_log(node, upid, start=start, limit=limit)
            
            return Response({
                'log': log_lines,
                'start': start,
                'total': len(log_lines)
            })
        except PVEServer.DoesNotExist:
            return Response({
                'detail': '服务器不存在或已禁用'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception('获取任务日志失败')
            return Response({
                'detail': f'获取任务日志失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='nodes/(?P<node>[^/.]+)/monitor')
    def node_monitor(self, request, pk=None, node=None):
        """获取节点监控数据（状态 + RRD 曲线）。"""
        server = self.get_object()
        timeframe = (request.query_params.get('timeframe') or 'hour').lower()
        cf = (request.query_params.get('cf') or 'AVERAGE').upper()
        datasource = request.query_params.get('ds')
        
        allowed_timeframes = {'hour', 'day', 'week', 'month', 'year'}
        if timeframe not in allowed_timeframes:
            timeframe = 'hour'
        allowed_cf = {'AVERAGE', 'MAX', 'MIN'}
        if cf not in allowed_cf:
            cf = 'AVERAGE'
        
        try:
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            status_data = client.get_node_status(node)
            rrd_raw = client.get_node_rrddata(node, timeframe=timeframe, cf=cf, datasource=datasource)
            metrics = self._normalize_rrd_metrics(rrd_raw)
            latest_metric = metrics[-1] if metrics else {}
            summary = self._build_node_summary(status_data, latest_metric)
            alerts = self._build_node_alerts(summary, status_data, latest_metric)
            
            return Response({
                'status': status_data,
                'summary': summary,
                'metrics': metrics,
                'alerts': alerts,
                'timeframe': timeframe,
                'cf': cf
            })
        except Exception as e:
            return Response({
                'detail': f'获取节点监控数据失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='next-vmid')
    def next_vmid(self, request, pk=None):
        """获取下一个可用的VMID。"""
        server = self.get_object()
        
        try:
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            # 获取下一个VMID
            vmid = client.get_next_vmid()
            return Response({'vmid': vmid})
        except Exception as e:
            return Response({
                'detail': f'获取下一个VMID失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _normalize_rrd_metrics(self, metrics):
        """整理RRD返回的数据，统一时间戳与数值类型。"""
        normalized = []
        if not isinstance(metrics, list):
            return normalized
        
        numeric_fields = {
            'cpu', 'iowait', 'mem', 'maxmem', 'disk', 'maxdisk',
            'netin', 'netout', 'loadavg', 'maxcpu', 'maxnet',
            'swap', 'maxswap'
        }
        for item in metrics:
            if not isinstance(item, dict):
                continue
            record = {}
            try:
                timestamp = item.get('time')
                if timestamp is not None:
                    record['time'] = int(float(timestamp)) * 1000
            except (ValueError, TypeError):
                continue
            
            for field in numeric_fields:
                if field not in item or item[field] is None:
                    continue
                value = item[field]
                try:
                    if field in {'mem', 'maxmem', 'disk', 'maxdisk', 'netin', 'netout', 'maxnet', 'swap', 'maxswap'}:
                        record[field] = int(float(value))
                    else:
                        record[field] = float(value)
                except (ValueError, TypeError):
                    continue
            if record:
                normalized.append(record)
        
        normalized.sort(key=lambda x: x.get('time', 0))
        return normalized
    
    def _build_node_summary(self, status_data, latest_metric):
        """根据节点状态与最新RRD数据构建汇总信息。"""
        status_data = status_data or {}
        latest_metric = latest_metric or {}
        
        def safe_percent(used, total):
            try:
                used = float(used or 0)
                total = float(total or 0)
                if total <= 0:
                    return 0
                return round((used / total) * 100, 2)
            except (ValueError, TypeError, ZeroDivisionError):
                return 0
        
        cpu_ratio = status_data.get('cpu')
        if cpu_ratio is None:
            cpu_ratio = latest_metric.get('cpu')
        try:
            cpu_percent = round(float(cpu_ratio or 0) * 100, 2)
        except (ValueError, TypeError):
            cpu_percent = 0
        
        max_cpu = status_data.get('maxcpu') or latest_metric.get('maxcpu') or 0
        mem_total = status_data.get('maxmem') or latest_metric.get('maxmem') or 0
        mem_used = status_data.get('mem') or latest_metric.get('mem') or 0
        rootfs = status_data.get('rootfs') or {}
        disk_total = (
            rootfs.get('total')
            or status_data.get('maxdisk')
            or latest_metric.get('maxdisk')
            or 0
        )
        disk_used = (
            rootfs.get('used')
            or status_data.get('disk')
            or latest_metric.get('disk')
            or 0
        )
        net_in = latest_metric.get('netin') or 0
        net_out = latest_metric.get('netout') or 0
        
        summary = {
            'cpu': {
                'percent': cpu_percent,
                'cores': int(max_cpu) if max_cpu else 0,
                'loadavg': status_data.get('loadavg') or latest_metric.get('loadavg')
            },
            'memory': {
                'total': int(mem_total),
                'used': int(mem_used),
                'percent': safe_percent(mem_used, mem_total)
            },
            'storage': {
                'total': int(disk_total),
                'used': int(disk_used),
                'percent': safe_percent(disk_used, disk_total)
            },
            'network': {
                'in': int(net_in),
                'out': int(net_out)
            },
            'uptime': status_data.get('uptime') or 0,
            'node': status_data.get('node'),
            'status': status_data.get('status'),
            'pveversion': status_data.get('pveversion'),
            'last_update': latest_metric.get('time')
        }
        return summary
    
    def _build_node_alerts(self, summary, status_data, latest_metric):
        """根据汇总信息生成健康告警。"""
        summary = summary or {}
        status_data = status_data or {}
        alerts = []
        
        status_text = (status_data.get('status') or '').lower()
        if status_text and status_text not in {'online', 'running'}:
            alerts.append({
                'level': 'danger',
                'message': f'节点状态异常：{status_data.get("status") or "未知"}'
            })
        
        level = status_data.get('level')
        if level and str(level).lower() in {'warning', 'alert', 'critical'}:
            alerts.append({
                'level': 'warning' if str(level).lower() == 'warning' else 'danger',
                'message': f'PVE上报节点等级：{level}'
            })
        
        cpu_percent = (summary.get('cpu') or {}).get('percent') or 0
        if cpu_percent >= 90:
            alerts.append({'level': 'danger', 'message': f'CPU使用率达到 {cpu_percent}%（>=90%）'})
        elif cpu_percent >= 75:
            alerts.append({'level': 'warning', 'message': f'CPU使用率较高：{cpu_percent}%（>=75%）'})
        
        mem_percent = (summary.get('memory') or {}).get('percent') or 0
        if mem_percent >= 90:
            alerts.append({'level': 'danger', 'message': f'内存使用率达到 {mem_percent}%（>=90%）'})
        elif mem_percent >= 80:
            alerts.append({'level': 'warning', 'message': f'内存使用率较高：{mem_percent}%（>=80%）'})
        
        disk_percent = (summary.get('storage') or {}).get('percent') or 0
        if disk_percent >= 90:
            alerts.append({'level': 'danger', 'message': f'存储使用率达到 {disk_percent}%（>=90%）'})
        elif disk_percent >= 80:
            alerts.append({'level': 'warning', 'message': f'存储使用率较高：{disk_percent}%（>=80%）'})
        
        loadavg = status_data.get('loadavg') or latest_metric.get('loadavg')
        cores = (summary.get('cpu') or {}).get('cores') or 1
        try:
            if isinstance(loadavg, (list, tuple)) and loadavg:
                load_value = float(loadavg[0])
            else:
                load_value = float(loadavg)
            if load_value > cores * 1.5:
                alerts.append({
                    'level': 'warning',
                    'message': f'负载值 {load_value:.2f} 高于CPU核心数 {cores}'
                })
        except (TypeError, ValueError):
            pass
        
        return alerts


class VirtualMachineViewSet(AuditOwnerPopulateMixin, ActionSerializerMixin, viewsets.ModelViewSet):
    """虚拟机CRUD视图集。"""
    
    queryset = VirtualMachine.objects.all().order_by('-created_at')
    
    serializer_class = VirtualMachineDetailSerializer
    list_serializer_class = VirtualMachineListSerializer
    retrieve_serializer_class = VirtualMachineDetailSerializer
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['server', 'status', 'node']
    search_fields = ['name', 'vmid', 'ip_address']
    ordering_fields = ['id', 'vmid', 'name', 'created_at']
    
    @action(detail=False, methods=['post'])
    def create_vm(self, request):
        """创建虚拟机。"""
        serializer = VirtualMachineCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        server_id = data['server_id']
        node = data['node']
        
        try:
            server = PVEServer.objects.get(id=server_id, is_active=True)
        except PVEServer.DoesNotExist:
            return Response({
                'detail': 'PVE服务器不存在或未启用'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 创建PVE客户端
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            # 构建虚拟机配置
            vmid = data.get('vmid')
            # 解析磁盘大小（默认10GB，最小1GB）
            raw_disk_size = data.get('disk_size', 10) or 10
            try:
                disk_size_gb = int(raw_disk_size)
            except (ValueError, TypeError):
                logger.warning(f'无法解析磁盘大小 {raw_disk_size}，使用默认值10GB')
                disk_size_gb = 10
            if disk_size_gb < 1:
                disk_size_gb = 1
            disk_size_str = f'{disk_size_gb}G'
            
            # 构建PVE API参数（使用URL参数，表单格式）
            # PVE API创建虚拟机使用URL参数，所有配置都作为URL参数传递
            params = {
                'vmid': vmid,
                'name': str(data['name']),
                'sockets': int(data.get('sockets', 1)),
                'cores': int(data.get('cores', 1)),
                'cpu': str(data.get('cpu', 'x86-64-v2-AES')),
                'memory': int(data.get('memory', 512)),
                'ostype': str(data.get('ostype', 'l26')),
                'scsihw': str(data.get('scsihw', 'virtio-scsi-single')),
                'numa': 1 if data.get('numa', False) else 0,  # NUMA设置，转换为0或1
            }
            
            # 磁盘配置 - PVE API格式根据存储类型不同
            disk_storage = data.get('disk_storage')
            if disk_storage:
                # 获取存储信息以确定存储类型
                try:
                    storages = client.get_storage(node)
                    storage_info = next((s for s in storages if s.get('storage') == disk_storage), None)
                    storage_type = storage_info.get('type') if storage_info else None
                    
                    # 根据存储类型使用不同的格式
                    if storage_type == 'rbd':
                        # RBD/Ceph存储格式：scsi0=storage:size（数字，无单位）
                        # 例如：ceph:32 表示32GB
                        params['scsi0'] = f'{disk_storage}:{disk_size_gb}'
                        # 可选：添加iothread参数提升性能
                        params['scsi0'] += ',iothread=on'
                    elif storage_type == 'lvm' or storage_type == 'lvmthin':
                        # LVM/LVM-Thin存储格式：scsi0=storage:size（数字，无单位）
                        # 例如：local-lvm:32 表示32GB
                        params['scsi0'] = f'{disk_storage}:{disk_size_gb}'
                    else:
                        # 其他存储类型（如dir, nfs等）使用标准格式：scsi0=storage:size（带单位）
                        params['scsi0'] = f'{disk_storage}:{disk_size_str}'
                except Exception as e:
                    # 如果获取存储信息失败，尝试根据存储名称判断
                    logger.warning(f'获取存储信息失败: {str(e)}')
                    # 如果存储名称包含ceph、rbd、lvm，使用数字格式
                    if 'ceph' in disk_storage.lower() or 'rbd' in disk_storage.lower():
                        params['scsi0'] = f'{disk_storage}:{disk_size_gb},iothread=on'
                    elif 'lvm' in disk_storage.lower():
                        params['scsi0'] = f'{disk_storage}:{disk_size_gb}'
                    else:
                        params['scsi0'] = f'{disk_storage}:{disk_size_str}'
            
            # 网络配置 - PVE API格式：net0=model,bridge=bridge_name,firewall=0|1
            network_bridge = str(data.get('network_bridge', 'vmbr0'))
            network_firewall = 1 if data.get('network_firewall', True) else 0
            params['net0'] = f'virtio,bridge={network_bridge},firewall={network_firewall}'
            
            # ISO配置（如果有）- PVE API格式：ide2=storage:iso/file.iso,media=cdrom
            if data.get('iso'):
                iso_value = str(data['iso'])
                # 如果ISO值是完整路径（如 storage:iso/file.iso），直接使用
                if ':' in iso_value:
                    params['ide2'] = f'{iso_value},media=cdrom'
                else:
                    # 否则使用iso_storage或disk_storage拼接
                    iso_storage = data.get('iso_storage') or disk_storage
                    if iso_storage:
                        params['ide2'] = f'{iso_storage}:iso/{iso_value},media=cdrom'
            
            # 描述（如果有）
            if data.get('description'):
                params['description'] = str(data['description'])
            
            # 记录配置信息用于调试
            logger.info(f'创建虚拟机参数: vmid={vmid}, node={node}, params={params}')
            config_snapshot = params.copy()
            
            # 创建虚拟机 - 传递params作为URL参数
            result = client.create_vm(node, vmid, params)
            
            # 等待任务完成（简化处理，实际应该轮询任务状态）
            # 这里先创建数据库记录
            vm = VirtualMachine.objects.create(
                server=server,
                vmid=vmid,
                name=data['name'],
                node=node,
                status='stopped',
                cpu_cores=data.get('cores', 1),
                memory_mb=data.get('memory', 512),
                disk_gb=disk_size_gb,
                description=data.get('description', ''),
                pve_config=config_snapshot,
                created_by=request.user if request.user.is_authenticated else None,
            )
            
            serializer = VirtualMachineDetailSerializer(vm)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'detail': f'创建虚拟机失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def vm_action(self, request, pk=None):
        """虚拟机操作（启动、停止、重启等）。"""
        vm = self.get_object()
        serializer = VirtualMachineActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        
        try:
            server = vm.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            if action_type == 'start':
                result = client.start_vm(vm.node, vm.vmid)
                vm.status = 'running'
            elif action_type == 'stop':
                result = client.stop_vm(vm.node, vm.vmid)
                vm.status = 'stopped'
            elif action_type == 'shutdown':
                result = client.shutdown_vm(vm.node, vm.vmid)
                vm.status = 'stopped'
            elif action_type == 'reboot':
                result = client.reboot_vm(vm.node, vm.vmid)
                vm.status = 'running'
            else:
                return Response({
                    'detail': f'不支持的操作: {action_type}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            vm.save()
            
            return Response({
                'success': True,
                'message': f'操作 {action_type} 已提交',
                'upid': result
            })
            
        except Exception as e:
            return Response({
                'detail': f'操作失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='update-hardware')
    def update_hardware(self, request, pk=None):
        """更新虚拟机硬件配置。"""
        vm = self.get_object()
        serializer = VirtualMachineHardwareUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data.get('params', {})
        
        if not params:
            return Response({
                'detail': '缺少需要更新的配置参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            server = vm.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            result = client.update_vm_config(vm.node, vm.vmid, params)
            
            # 更新数据库中的缓存配置
            config = client.get_vm_config(vm.node, vm.vmid)
            vm.pve_config = config
            if 'cores' in config and 'sockets' in config:
                vm.cpu_cores = config['cores'] * config['sockets']
            elif 'cores' in config:
                vm.cpu_cores = config['cores']
            if 'memory' in config:
                vm.memory_mb = config['memory']
            vm.save()
            
            return Response({
                'success': True,
                'message': '硬件配置更新已提交',
                'upid': result,
                'config': config
            })
        except Exception as e:
            logger.exception('更新虚拟机硬件配置失败')
            return Response({
                'detail': f'更新虚拟机硬件配置失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'post'])
    def options(self, request, pk=None):
        """获取或更新虚拟机选项配置。"""
        vm = self.get_object()
        try:
            server = vm.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            if request.method.lower() == 'get':
                config = client.get_vm_config(vm.node, vm.vmid)
                vm.pve_config = config
                vm.save(update_fields=['pve_config'])
                return Response({
                    'config': config
                })
            serializer = VMOptionsUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            params = serializer.validated_data.get('params', {})
            if not params:
                return Response({
                    'detail': '缺少需要更新的选项参数'
                }, status=status.HTTP_400_BAD_REQUEST)
            result = client.update_vm_config(vm.node, vm.vmid, params)
            config = client.get_vm_config(vm.node, vm.vmid)
            vm.pve_config = config
            vm.save(update_fields=['pve_config'])
            return Response({
                'success': True,
                'message': '选项配置更新已提交',
                'upid': result,
                'config': config
            })
        except Exception as e:
            logger.exception('处理虚拟机选项请求失败')
            return Response({
                'detail': f'处理虚拟机选项请求失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """克隆虚拟机。"""
        vm = self.get_object()
        serializer = VMCloneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            server = vm.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            new_vmid = data.get('new_vmid')
            if not new_vmid:
                new_vmid = client.get_next_vmid()
            clone_result = client.clone_vm(
                vm.node,
                newid=new_vmid,
                source_vmid=vm.vmid,
                name=data.get('name'),
                full=data.get('full', False),
                target=data.get('target_node'),
                storage=data.get('storage'),
                disk_format=data.get('disk_format'),
                description=data.get('description'),
                pool=data.get('pool'),
                snapname=data.get('snapname')
            )
            return Response({
                'success': True,
                'message': '克隆任务已提交',
                'upid': clone_result,
                'new_vmid': new_vmid
            })
        except Exception as e:
            logger.exception('克隆虚拟机失败')
            return Response({
                'detail': f'克隆虚拟机失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='console-session')
    def console_session(self, request, pk=None):
        """创建noVNC会话，返回WebSocket连接信息。"""
        vm = self.get_object()
        session_type = request.data.get('type', 'novnc')
        if session_type != 'novnc':
            return Response({
                'detail': '当前仅支持 noVNC 会话'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            server = vm.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            proxy = client.create_vnc_proxy(vm.node, vm.vmid, websocket=True)
            port = proxy.get('port')
            ticket = proxy.get('ticket')
            password = proxy.get('password')
            cert = proxy.get('cert')
            
            if not port or not ticket:
                raise Exception('PVE未返回有效的VNC代理信息')
            
            encoded_ticket = quote_plus(ticket)
            websocket_url = (
                f"wss://{server.host}:{server.port}/api2/json/nodes/{vm.node}/qemu/{vm.vmid}/"
                f"vncwebsocket?port={port}&vncticket={encoded_ticket}"
            )
            
            session_token = secrets.token_urlsafe(32)
            proxy_path = f"/ws/pve/console/{vm.id}/?token={session_token}"
            cache_key = f"{SESSION_CACHE_PREFIX}{session_token}"
            cache.set(cache_key, {
                'websocket_url': websocket_url,
                'ticket': ticket,
                'port': port,
                'password': password,
                'vmid': vm.vmid,
                'vm_pk': vm.pk,
                'node': vm.node,
                'server_id': server.id,
                'vm_name': vm.name,
                'console_type': 'kvm',
                'proxy_path': proxy_path,
                'origin': f"https://{server.host}:{server.port}",
            }, timeout=PVE_CONSOLE_SESSION_TTL)
            proxy_scheme = 'wss' if request.is_secure() else 'ws'
            proxy_url = f"{proxy_scheme}://{request.get_host()}{proxy_path}"
            
            return Response({
                'websocket_url': websocket_url,
                'ticket': ticket,
                'password': password,
                'port': port,
                'node': vm.node,
                'vmid': vm.vmid,
                'cert': cert,
                'proxy_path': proxy_path,
                'proxy_url': proxy_url,
                'session_token': session_token,
                'server': {
                    'host': server.host,
                    'port': server.port,
                    'verify_ssl': server.verify_ssl
                }
            })
        except Exception as e:
            logger.exception('创建noVNC会话失败')
            return Response({
                'detail': f'创建控制台会话失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def backups(self, request, pk=None):
        """获取虚拟机备份列表及可用存储。"""
        vm = self.get_object()
        try:
            server = vm.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            storages = client.get_storage(vm.node)
            backup_storages = []
            backups = []

            def supports_backup(storage_item):
                content = storage_item.get('content')
                if isinstance(content, str):
                    entries = [c.strip() for c in content.split(',') if c.strip()]
                elif isinstance(content, (list, tuple)):
                    entries = list(content)
                else:
                    entries = []
                return 'backup' in entries

            for storage in storages:
                if not supports_backup(storage):
                    continue
                storage_name = storage.get('storage')
                backup_storages.append({
                    'storage': storage_name,
                    'type': storage.get('type'),
                    'content': storage.get('content'),
                    'shared': storage.get('shared'),
                    'enabled': storage.get('enabled', 1),
                    'total': storage.get('total'),
                    'avail': storage.get('avail')
                })
                try:
                    contents = client.get_storage_content(vm.node, storage_name, content_type='backup')
                except Exception as e:
                    logger.warning('获取备份列表失败 storage=%s: %s', storage_name, e)
                    continue
                for item in contents or []:
                    if item.get('vmid') and str(item.get('vmid')) != str(vm.vmid):
                        continue
                    backups.append({
                        'storage': storage_name,
                        'volid': item.get('volid'),
                        'size': item.get('size'),
                        'format': item.get('format'),
                        'ctime': item.get('ctime'),
                        'notes': item.get('notes'),
                        'vmid': item.get('vmid')
                    })

            return Response({
                'backups': backups,
                'storages': backup_storages
            })
        except Exception as e:
            logger.exception('获取备份列表失败')
            return Response({
                'detail': f'获取备份列表失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def create_backup(self, request, pk=None):
        """创建虚拟机备份。"""
        vm = self.get_object()
        serializer = VMBackupCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            server = vm.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            result = client.create_backup(
                vm.node,
                vm.vmid,
                storage=data['storage'],
                mode=data.get('mode', 'snapshot'),
                compress=data.get('compress', 'zstd'),
                remove=data.get('remove', False),
                notes=data.get('notes', '')
            )
            return Response({
                'success': True,
                'upid': result
            })
        except Exception as e:
            logger.exception('创建备份任务失败')
            return Response({
                'detail': f'创建备份失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def snapshots(self, request, pk=None):
        """获取虚拟机快照列表。"""
        vm = self.get_object()
        try:
            server = vm.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            raw_snapshots = client.list_snapshots(vm.node, vm.vmid) or []

            flat = []

            def traverse(items, parent=None):
                for item in items or []:
                    name = item.get('name')
                    entry = {
                        'name': name,
                        'description': item.get('description', ''),
                        'snaptime': item.get('snaptime'),
                        'parent': parent,
                        'state': item.get('state'),
                        'vmstate': item.get('vmstate', False),
                        'running': item.get('running'),
                        'is_current': name == 'current' or item.get('current', False)
                    }
                    flat.append(entry)
                    children = item.get('children') or []
                    if children:
                        traverse(children, name)

            traverse(raw_snapshots, None)
            return Response({'snapshots': flat})
        except Exception as e:
            logger.exception('获取快照列表失败')
            return Response({
                'detail': f'获取快照列表失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def create_snapshot(self, request, pk=None):
        """创建虚拟机快照。"""
        vm = self.get_object()
        serializer = VMSnapshotCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            server = vm.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            result = client.create_snapshot(
                vm.node,
                vm.vmid,
                name=data['name'],
                description=data.get('description', ''),
                include_memory=data.get('include_memory', False)
            )
            return Response({
                'success': True,
                'upid': result
            })
        except Exception as e:
            logger.exception('创建快照失败')
            return Response({
                'detail': f'创建快照失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def rollback_snapshot(self, request, pk=None):
        """回滚到指定快照。"""
        vm = self.get_object()
        serializer = VMSnapshotActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            server = vm.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            result = client.rollback_snapshot(vm.node, vm.vmid, data['name'])
            return Response({
                'success': True,
                'upid': result
            })
        except Exception as e:
            logger.exception('回滚快照失败')
            return Response({
                'detail': f'回滚快照失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def delete_snapshot(self, request, pk=None):
        """删除指定快照。"""
        vm = self.get_object()
        serializer = VMSnapshotActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            server = vm.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            result = client.delete_snapshot(vm.node, vm.vmid, data['name'])
            return Response({
                'success': True,
                'upid': result
            })
        except Exception as e:
            logger.exception('删除快照失败')
            return Response({
                'detail': f'删除快照失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """获取虚拟机任务历史列表。"""
        vm = self.get_object()
        try:
            server = vm.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            limit = int(request.query_params.get('limit', 100))
            statusfilter = request.query_params.get('task_status')
            if not statusfilter or statusfilter.lower() == 'all':
                statusfilter = None
            tasks = client.list_tasks(
                vm.node,
                vmid=vm.vmid,
                limit=limit,
                statusfilter=statusfilter
            )
            
            # 过滤与当前虚拟机相关的任务（再次确认）
            filtered_tasks = []
            for task in tasks:
                # PVE 任务 ID 格式通常包含 vmid，但为了更精确，检查 upid
                upid = task.get('upid', '')
                task_type = task.get('type', '')
                
                # 检查任务是否与当前 VM 相关
                # upid 格式: UPID:node:pid:pstart:task_id:type:vmid:user@realm:
                if str(vm.vmid) in upid or task_type in ['qmstart', 'qmstop', 'qmshutdown', 'qmreboot', 'qmrestore', 'vzdump', 'qmsnapshot']:
                    filtered_tasks.append({
                        'upid': upid,
                        'type': task_type,
                        'status': task.get('status', 'unknown'),
                        'starttime': task.get('starttime'),
                        'endtime': task.get('endtime'),
                        'user': task.get('user'),
                        'node': task.get('node'),
                        'pid': task.get('pid'),
                        'pstart': task.get('pstart'),
                        'id': task.get('id')
                    })
            
            return Response({'tasks': filtered_tasks})
        except Exception as e:
            logger.exception('获取任务列表失败')
            return Response({
                'detail': f'获取任务列表失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='task-log')
    def task_log(self, request, pk=None):
        """获取任务日志。"""
        vm = self.get_object()
        upid = request.data.get('upid')
        if not upid:
            return Response({
                'detail': '缺少 upid 参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            server = vm.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            start = int(request.data.get('start', 0))
            limit = int(request.data.get('limit', 200))
            log_lines = client.get_task_log(vm.node, upid, start=start, limit=limit)
            
            return Response({
                'log': log_lines,
                'start': start,
                'total': len(log_lines)
            })
        except Exception as e:
            logger.exception('获取任务日志失败')
            return Response({
                'detail': f'获取任务日志失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='sync_all')
    def sync_all(self, request):
        """同步PVE中现有的虚拟机到本地数据库，可按服务器筛选。"""
        server_id = request.data.get('server_id')
        
        servers_qs = PVEServer.objects.filter(is_active=True)
        if server_id:
            servers_qs = servers_qs.filter(id=server_id)
            if not servers_qs.exists():
                return Response(
                    {'detail': '指定的PVE服务器不存在或已禁用'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        summary = {
            'server_count': servers_qs.count(),
            'synced': 0,
            'created': 0,
            'updated': 0,
            'errors': []
        }
        
        def _extract_disk_gb(vm_config, vm_info):
            candidates = ['scsi0', 'virtio0', 'sata0', 'ide0']
            for field in candidates:
                value = vm_config.get(field)
                if isinstance(value, str) and 'size=' in value:
                    size_part = value.split('size=', 1)[1].split(',', 1)[0].strip().upper()
                    if size_part.endswith('G'):
                        try:
                            return int(size_part[:-1])
                        except ValueError:
                            continue
                    if size_part.endswith('M'):
                        try:
                            return max(1, int(size_part[:-1]) // 1024)
                        except ValueError:
                            continue
            maxdisk = vm_info.get('maxdisk')
            if isinstance(maxdisk, (int, float)) and maxdisk > 0:
                return max(1, int(maxdisk // (1024 * 1024 * 1024)))
            return 10
        
        def _extract_ip(vm_config):
            ipconfig = vm_config.get('ipconfig0')
            if isinstance(ipconfig, str) and 'ip=' in ipconfig:
                try:
                    ip_part = ipconfig.split('ip=', 1)[1].split(',', 1)[0]
                    return ip_part.split('/')[0]
                except Exception:
                    return ''
            return ''
        
        for server in servers_qs:
            try:
                client = PVEAPIClient(
                    host=server.host,
                    port=server.port,
                    token_id=server.token_id,
                    token_secret=server.token_secret,
                    verify_ssl=server.verify_ssl
                )
                nodes = client.get_nodes()
                nodes = nodes if isinstance(nodes, list) else [nodes] if nodes else []
            except Exception as exc:
                summary['errors'].append(f'{server.name}: {exc}')
                continue
            
            for node_info in nodes:
                node_name = node_info.get('node') or node_info.get('name')
                if not node_name:
                    continue
                try:
                    vm_list = client.get_vms(node_name) or []
                except Exception as exc:
                    summary['errors'].append(f'{server.name}/{node_name}: {exc}')
                    continue
                
                for vm_info in vm_list:
                    vmid = vm_info.get('vmid') or vm_info.get('vmid')
                    try:
                        vmid = int(vmid)
                    except (TypeError, ValueError):
                        continue
                    
                    try:
                        vm_config = client.get_vm_config(node_name, vmid)
                    except Exception:
                        vm_config = {}
                    
                    cpu_cores = (
                        vm_config.get('cores')
                        or vm_info.get('cores')
                        or vm_info.get('cpus')
                        or vm_info.get('maxcpu')
                        or 1
                    )
                    try:
                        cpu_cores = int(cpu_cores)
                    except (TypeError, ValueError):
                        cpu_cores = 1
                    
                    memory_mb = vm_config.get('memory')
                    if not memory_mb:
                        maxmem = vm_info.get('maxmem')
                        if isinstance(maxmem, (int, float)):
                            memory_mb = max(1, int(maxmem // (1024 * 1024)))
                        else:
                            memory_mb = 512
                    
                    disk_gb = _extract_disk_gb(vm_config, vm_info)
                    ip_address = _extract_ip(vm_config)
                    description = vm_config.get('description') or vm_config.get('notes', '')
                    status_value = vm_info.get('status', 'unknown')
                    if status_value not in dict(VirtualMachine.STATUS_CHOICES):
                        status_value = 'unknown'
                    
                    defaults = {
                        'name': vm_info.get('name') or f'vm-{vmid}',
                        'node': node_name,
                        'status': status_value,
                        'cpu_cores': cpu_cores,
                        'memory_mb': memory_mb,
                        'disk_gb': disk_gb,
                        'ip_address': ip_address,
                        'description': description or '',
                        'pve_config': vm_config or vm_info,
                    }
                    
                    with transaction.atomic():
                        vm_obj, created = VirtualMachine.objects.update_or_create(
                            server=server,
                            vmid=vmid,
                            defaults=defaults
                        )
                        summary['synced'] += 1
                        if created:
                            summary['created'] += 1
                        else:
                            summary['updated'] += 1
        
        return Response(summary)
    
    @action(detail=True, methods=['get'])
    def sync_status(self, request, pk=None):
        """同步虚拟机状态。"""
        vm = self.get_object()
        
        try:
            server = vm.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            # 获取虚拟机状态
            status_info = client.get_vm_status(vm.node, vm.vmid)
            config = client.get_vm_config(vm.node, vm.vmid)
            
            # 更新状态
            qmpstatus = status_info.get('status', 'unknown')
            if qmpstatus == 'running':
                vm.status = 'running'
            elif qmpstatus == 'stopped':
                vm.status = 'stopped'
            else:
                vm.status = 'unknown'
            
            # 更新配置信息
            vm.pve_config = config
            if 'cores' in config:
                vm.cpu_cores = config['cores']
            if 'memory' in config:
                vm.memory_mb = config['memory']
            
            vm.save()
            
            serializer = VirtualMachineDetailSerializer(vm)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                'detail': f'同步状态失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class LXCContainerViewSet(AuditOwnerPopulateMixin, ActionSerializerMixin, viewsets.ModelViewSet):
    """LXC容器管理视图集。"""
    
    queryset = LXCContainer.objects.all().order_by('-created_at')
    
    serializer_class = LXCContainerDetailSerializer
    list_serializer_class = LXCContainerListSerializer
    retrieve_serializer_class = LXCContainerDetailSerializer
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['server', 'status', 'node']
    search_fields = ['name', 'vmid', 'ip_address']
    ordering_fields = ['id', 'vmid', 'name', 'created_at']
    
    @action(detail=True, methods=['post'])
    def container_action(self, request, pk=None):
        """容器操作（启动、停止、关闭、重启）。"""
        container = self.get_object()
        serializer = LXCContainerActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action_type = serializer.validated_data['action']
        
        try:
            server = container.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            
            if action_type == 'start':
                result = client.start_container(container.node, container.vmid)
                container.status = 'running'
            elif action_type == 'stop':
                result = client.stop_container(container.node, container.vmid)
                container.status = 'stopped'
            elif action_type == 'shutdown':
                result = client.shutdown_container(container.node, container.vmid)
                container.status = 'stopped'
            elif action_type == 'reboot':
                result = client.reboot_container(container.node, container.vmid)
                container.status = 'running'
            else:
                return Response({'detail': f'不支持的操作: {action_type}'}, status=status.HTTP_400_BAD_REQUEST)
            
            container.save(update_fields=['status'])
            return Response({
                'success': True,
                'message': f'容器操作 {action_type} 已提交',
                'upid': result
            })
        except Exception as exc:
            logger.exception('执行容器操作失败')
            return Response({
                'detail': f'执行容器操作失败: {str(exc)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def sync_status(self, request, pk=None):
        """同步容器状态。"""
        container = self.get_object()
        try:
            server = container.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                token_id=server.token_id,
                token_secret=server.token_secret,
                verify_ssl=server.verify_ssl
            )
            status_info = client.get_container_status(container.node, container.vmid)
            config = client.get_container_config(container.node, container.vmid)
            
            qstatus = status_info.get('status', 'unknown')
            if qstatus in dict(LXCContainer.STATUS_CHOICES):
                container.status = qstatus
            else:
                container.status = 'unknown'
            
            container.pve_config = config
            if 'cores' in config:
                container.cpu_cores = config.get('cores') or container.cpu_cores
            if 'memory' in config:
                container.memory_mb = config.get('memory') or container.memory_mb
            container.save()
            
            serializer = LXCContainerDetailSerializer(container)
            return Response(serializer.data)
        except Exception as exc:
            logger.exception('同步容器状态失败')
            return Response({
                'detail': f'同步容器状态失败: {str(exc)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='sync_all')
    def sync_all(self, request):
        """同步PVE中的LXC容器。"""
        server_id = request.data.get('server_id')
        servers_qs = PVEServer.objects.filter(is_active=True)
        if server_id:
            servers_qs = servers_qs.filter(id=server_id)
            if not servers_qs.exists():
                return Response(
                    {'detail': '指定的PVE服务器不存在或已禁用'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        summary = {
            'server_count': servers_qs.count(),
            'synced': 0,
            'created': 0,
            'updated': 0,
            'errors': []
        }
        
        def _extract_disk_gb(config, info):
            rootfs = config.get('rootfs') or info.get('rootfs') or ''
            if isinstance(rootfs, str) and 'size=' in rootfs:
                size_part = rootfs.split('size=', 1)[1].split(',', 1)[0].strip().upper()
                if size_part.endswith('G'):
                    try:
                        return int(size_part[:-1])
                    except ValueError:
                        pass
                if size_part.endswith('M'):
                    try:
                        return max(1, int(size_part[:-1]) // 1024)
                    except ValueError:
                        pass
            maxdisk = info.get('maxdisk')
            if isinstance(maxdisk, (int, float)) and maxdisk > 0:
                return max(1, int(maxdisk // (1024 * 1024 * 1024)))
            return 10
        
        def _extract_ip(config):
            ip_fields = [config.get('ipconfig0'), config.get('net0')]
            for field in ip_fields:
                if isinstance(field, str) and 'ip=' in field:
                    try:
                        ip_part = field.split('ip=', 1)[1].split(',', 1)[0]
                        return ip_part.split('/')[0]
                    except Exception:
                        continue
            return ''
        
        for server in servers_qs:
            try:
                client = PVEAPIClient(
                    host=server.host,
                    port=server.port,
                    token_id=server.token_id,
                    token_secret=server.token_secret,
                    verify_ssl=server.verify_ssl
                )
                nodes = client.get_nodes()
                nodes = nodes if isinstance(nodes, list) else [nodes] if nodes else []
            except Exception as exc:
                summary['errors'].append(f'{server.name}: {exc}')
                continue
            
            for node_info in nodes:
                node_name = node_info.get('node') or node_info.get('name')
                if not node_name:
                    continue
                try:
                    container_list = client.get_lxc_containers(node_name) or []
                except Exception as exc:
                    summary['errors'].append(f'{server.name}/{node_name}: {exc}')
                    continue
                
                for container_info in container_list:
                    vmid = container_info.get('vmid')
                    try:
                        vmid = int(vmid)
                    except (TypeError, ValueError):
                        continue
                    
                    try:
                        config = client.get_container_config(node_name, vmid)
                    except Exception:
                        config = {}
                    
                    cpu_cores = (
                        config.get('cores')
                        or config.get('cpus')
                        or container_info.get('cores')
                        or container_info.get('cpus')
                        or 1
                    )
                    try:
                        cpu_cores = int(cpu_cores)
                    except (TypeError, ValueError):
                        cpu_cores = 1
                    
                    memory_mb = config.get('memory')
                    if not memory_mb:
                        maxmem = container_info.get('maxmem')
                        if isinstance(maxmem, (int, float)):
                            memory_mb = max(1, int(maxmem // (1024 * 1024)))
                        else:
                            memory_mb = 512
                    
                    disk_gb = _extract_disk_gb(config, container_info)
                    ip_address = _extract_ip(config)
                    description = config.get('description') or config.get('notes', '')
                    status_value = container_info.get('status', 'unknown')
                    if status_value not in dict(LXCContainer.STATUS_CHOICES):
                        status_value = 'unknown'
                    
                    defaults = {
                        'name': container_info.get('name') or config.get('hostname') or f'ct-{vmid}',
                        'node': node_name,
                        'status': status_value,
                        'cpu_cores': cpu_cores,
                        'memory_mb': memory_mb,
                        'disk_gb': disk_gb,
                        'ip_address': ip_address,
                        'description': description or '',
                        'pve_config': config or container_info,
                    }
                    
                    with transaction.atomic():
                        obj, created = LXCContainer.objects.update_or_create(
                            server=server,
                            vmid=vmid,
                            defaults=defaults
                        )
                        summary['synced'] += 1
                        if created:
                            summary['created'] += 1
                        else:
                            summary['updated'] += 1
        
        return Response(summary)


class NetworkTopologyViewSet(AuditOwnerPopulateMixin, ActionSerializerMixin, viewsets.ModelViewSet):
    """网络拓扑视图集：管理 LogicFlow 拓扑图。"""

    serializer_class = NetworkTopologyDetailSerializer
    list_serializer_class = NetworkTopologyListSerializer
    retrieve_serializer_class = NetworkTopologyDetailSerializer
    create_serializer_class = NetworkTopologySaveSerializer
    update_serializer_class = NetworkTopologySaveSerializer
    partial_update_serializer_class = NetworkTopologySaveSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['id', 'name', 'updated_at']

    def get_queryset(self):
        return NetworkTopology.objects.filter(is_deleted=False).order_by('-updated_at')

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user if self.request and self.request.user.is_authenticated else None,
            updated_by=self.request.user if self.request and self.request.user.is_authenticated else None,
        )

    def perform_update(self, serializer):
        serializer.save(
            updated_by=self.request.user if self.request and self.request.user.is_authenticated else None
        )


@login_required
def console_iframe_view(request):
    """内嵌noVNC的简单页面，由前端iframe加载。"""
    token = request.GET.get('token')
    if not token:
        return HttpResponseBadRequest('缺少token参数')
    
    cache_key = f"{SESSION_CACHE_PREFIX}{token}"
    session = cache.get(cache_key)
    if not session:
        return HttpResponseNotFound('控制台会话已过期，请重新打开')
    
    vm_pk = session.get('vm_pk')
    vm = None
    if vm_pk:
        vm = VirtualMachine.objects.filter(pk=vm_pk).select_related('server').first()
    if not vm:
        return HttpResponseBadRequest('找不到对应的虚拟机记录')
    
    vmid = session.get('vmid') or vm.vmid
    proxy_path = session.get('proxy_path') or f"/ws/pve/console/{vm.pk}/?token={token}"
    scheme = 'wss' if request.is_secure() else 'ws'
    proxy_ws_url = f"{scheme}://{request.get_host()}{proxy_path}"
    
    asset_placeholder = reverse('pve-console-asset', args=['__asset__'])
    asset_base = request.build_absolute_uri(asset_placeholder).rsplit('__asset__', 1)[0]
    
    console_config = {
        'ws_url': proxy_ws_url,
        'ws_path': proxy_path,
        'password': session.get('password', ''),
        'vmid': vmid,
        'vm_name': vm.name or '',
        'node': vm.node or '',
        'server_name': vm.server.name if vm.server else '',
        'console_type': session.get('console_type', 'kvm'),
        'auto_connect': True,
        'disable_commands': True,
    }
    
    context = {
        'ws_url': proxy_ws_url,
        'ws_path': proxy_path,
        'password': session.get('password', ''),
        'vmid': vmid,
        'vm_name': vm.name or '',
        'node': vm.node or '',
        'server_name': vm.server.name if vm.server else '',
        'console_type': session.get('console_type', 'kvm'),
        'asset_base': asset_base.rstrip('/'),
        'novnc_version': '1.6.0-2',
        'session_token': token,
        'console_config': json.dumps(console_config),
    }
    response = TemplateResponse(request, 'pve/console_iframe.html', context)
    response["X-Frame-Options"] = "ALLOWALL"
    response["Cross-Origin-Embedder-Policy"] = "unsafe-none"
    return response


def console_asset_view(request, path):
    """提供noVNC静态资源。"""
    normalized = path.strip('/')
    if not normalized:
        raise Http404("Invalid asset path")
    try:
        full_path = safe_join(str(NOVNC_ASSETS_DIR), normalized)
    except ValueError:
        raise Http404("Invalid asset path")

    target = Path(full_path)
    if not target.exists() or not target.is_file():
        raise Http404("Asset not found")

    mime, _ = mimetypes.guess_type(str(target))
    response = FileResponse(target.open('rb'), content_type=mime or 'application/octet-stream')
    response["Access-Control-Allow-Origin"] = "*"
    response["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response
