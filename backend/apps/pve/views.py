"""PVE模块视图集。"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import transaction

from apps.common.viewsets import ActionSerializerMixin
from apps.common.mixins import AuditOwnerPopulateMixin
from .models import PVEServer, VirtualMachine
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
)
from .pve_client import PVEAPIClient


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
                username=server.username,
                password=server.password,
                token_id=server.token_id,
                token_secret=server.token_secret,
                use_token=server.use_token,
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
                username=server.username,
                password=server.password,
                token_id=server.token_id,
                token_secret=server.token_secret,
                use_token=server.use_token,
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
                username=server.username,
                password=server.password,
                token_id=server.token_id,
                token_secret=server.token_secret,
                use_token=server.use_token,
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
                username=server.username,
                password=server.password,
                token_id=server.token_id,
                token_secret=server.token_secret,
                use_token=server.use_token,
                verify_ssl=server.verify_ssl
            )
            
            storage = client.get_storage(node)
            return Response(storage)
        except Exception as e:
            return Response({
                'detail': f'获取存储列表失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


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
                username=server.username,
                password=server.password,
                token_id=server.token_id,
                token_secret=server.token_secret,
                use_token=server.use_token,
                verify_ssl=server.verify_ssl
            )
            
            # 构建虚拟机配置
            vmid = data.get('vmid')
            if not vmid:
                # 如果没有指定vmid，从PVE API获取下一个可用的vmid
                vms = client.get_vms(node)
                existing_vmids = [vm.get('vmid') for vm in vms if 'vmid' in vm]
                vmid = max(existing_vmids) + 1 if existing_vmids else 100
            
            config = {
                'name': data['name'],
                'cores': data.get('cores', 1),
                'memory': data.get('memory', 512),
                'ostype': data.get('ostype', 'l26'),
            }
            
            # 磁盘配置
            disk_size = data.get('disk_size', '10G')
            disk_storage = data.get('disk_storage')
            if disk_storage:
                config['scsi0'] = f'{disk_storage}:{disk_size}'
            
            # 网络配置
            network_bridge = data.get('network_bridge', 'vmbr0')
            config['net0'] = f'virtio,bridge={network_bridge}'
            
            # ISO配置（如果有）
            if data.get('iso'):
                config['ide2'] = f'{disk_storage}:iso/{data["iso"]},media=cdrom'
            
            # 创建虚拟机
            result = client.create_vm(node, vmid, config)
            
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
                disk_gb=int(disk_size.replace('G', '')) if 'G' in disk_size else 10,
                description=data.get('description', ''),
                pve_config=config,
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
                username=server.username,
                password=server.password,
                token_id=server.token_id,
                token_secret=server.token_secret,
                use_token=server.use_token,
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
    
    @action(detail=True, methods=['get'])
    def sync_status(self, request, pk=None):
        """同步虚拟机状态。"""
        vm = self.get_object()
        
        try:
            server = vm.server
            client = PVEAPIClient(
                host=server.host,
                port=server.port,
                username=server.username,
                password=server.password,
                token_id=server.token_id,
                token_secret=server.token_secret,
                use_token=server.use_token,
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
