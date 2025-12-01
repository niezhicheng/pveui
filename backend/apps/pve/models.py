"""PVE 模块模型：PVE服务器配置和虚拟机管理。"""

from django.db import models
from apps.common.models import BaseAuditModel


class PVEServer(BaseAuditModel):
    """PVE服务器配置模型：存储PVE服务器的连接信息。"""
    
    name = models.CharField(max_length=100, verbose_name='服务器名称', help_text='PVE服务器的显示名称')
    host = models.CharField(max_length=255, verbose_name='服务器地址', help_text='PVE服务器IP或域名，如：192.168.1.100')
    port = models.IntegerField(default=8006, verbose_name='端口', help_text='PVE API端口，默认8006')
    token_id = models.CharField(max_length=100, verbose_name='Token ID', help_text='API Token ID')
    token_secret = models.CharField(max_length=255, verbose_name='Token Secret', help_text='API Token Secret')
    verify_ssl = models.BooleanField(default=False, verbose_name='验证SSL', help_text='是否验证SSL证书')
    is_active = models.BooleanField(default=True, verbose_name='是否启用', help_text='是否启用此服务器配置')
    
    class Meta:
        verbose_name = 'PVE服务器'
        verbose_name_plural = 'PVE服务器'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.host}:{self.port})"


class VirtualMachine(BaseAuditModel):
    """虚拟机模型：存储虚拟机信息。"""
    
    STATUS_CHOICES = [
        ('running', '运行中'),
        ('stopped', '已停止'),
        ('paused', '已暂停'),
        ('unknown', '未知'),
    ]
    
    server = models.ForeignKey(
        PVEServer,
        on_delete=models.CASCADE,
        related_name='virtual_machines',
        verbose_name='PVE服务器',
        help_text='所属的PVE服务器'
    )
    vmid = models.IntegerField(verbose_name='虚拟机ID', help_text='PVE中的虚拟机ID')
    name = models.CharField(max_length=255, verbose_name='虚拟机名称', help_text='虚拟机名称')
    node = models.CharField(max_length=100, verbose_name='节点', help_text='PVE节点名称')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unknown', verbose_name='状态')
    cpu_cores = models.IntegerField(default=1, verbose_name='CPU核心数')
    memory_mb = models.IntegerField(default=512, verbose_name='内存(MB)')
    disk_gb = models.IntegerField(default=10, verbose_name='磁盘(GB)')
    ip_address = models.CharField(max_length=255, blank=True, default='', verbose_name='IP地址', help_text='虚拟机IP地址')
    description = models.TextField(blank=True, default='', verbose_name='描述', help_text='虚拟机描述信息')
    pve_config = models.JSONField(default=dict, verbose_name='PVE配置', help_text='PVE中的完整配置信息（JSON格式）')
    
    class Meta:
        verbose_name = '虚拟机'
        verbose_name_plural = '虚拟机'
        unique_together = [['server', 'vmid']]
        indexes = [
            models.Index(fields=['server', 'vmid']),
            models.Index(fields=['status']),
            models.Index(fields=['node']),
        ]
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return f"{self.name} (VMID: {self.vmid})"


class LXCContainer(BaseAuditModel):
    """LXC容器模型：存储容器信息。"""
    
    STATUS_CHOICES = [
        ('running', '运行中'),
        ('stopped', '已停止'),
        ('paused', '已暂停'),
        ('unknown', '未知'),
    ]
    
    server = models.ForeignKey(
        PVEServer,
        on_delete=models.CASCADE,
        related_name='lxc_containers',
        verbose_name='PVE服务器',
        help_text='所属的PVE服务器'
    )
    vmid = models.IntegerField(verbose_name='容器ID', help_text='PVE中的容器ID')
    name = models.CharField(max_length=255, verbose_name='容器名称', help_text='容器名称')
    node = models.CharField(max_length=100, verbose_name='节点', help_text='PVE节点名称')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unknown', verbose_name='状态')
    cpu_cores = models.IntegerField(default=1, verbose_name='CPU核心数')
    memory_mb = models.IntegerField(default=512, verbose_name='内存(MB)')
    disk_gb = models.IntegerField(default=10, verbose_name='磁盘(GB)')
    ip_address = models.CharField(max_length=255, blank=True, default='', verbose_name='IP地址', help_text='容器IP地址')
    description = models.TextField(blank=True, default='', verbose_name='描述', help_text='容器描述信息')
    pve_config = models.JSONField(default=dict, verbose_name='PVE配置', help_text='PVE中的完整配置信息（JSON格式）')
    
    class Meta:
        verbose_name = 'LXC容器'
        verbose_name_plural = 'LXC容器'
        unique_together = [['server', 'vmid']]
        indexes = [
            models.Index(fields=['server', 'vmid']),
            models.Index(fields=['status']),
            models.Index(fields=['node']),
        ]
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return f"{self.name} (CTID: {self.vmid})"


class NetworkTopology(BaseAuditModel):
    """网络拓扑模型：保存LogicFlow图数据及元信息。"""

    name = models.CharField(max_length=150, verbose_name='拓扑名称')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    diagram_data = models.JSONField(default=dict, verbose_name='拓扑图数据')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='附加元信息')

    class Meta:
        verbose_name = '网络拓扑'
        verbose_name_plural = '网络拓扑'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self) -> str:
        return self.name
