"""PVE 模块模型：PVE服务器配置和虚拟机管理。"""

from django.db import models
from apps.common.models import BaseAuditModel


class PVEServer(BaseAuditModel):
    """PVE服务器配置模型：存储PVE服务器的连接信息。"""
    
    name = models.CharField(max_length=100, verbose_name='服务器名称', help_text='PVE服务器的显示名称')
    host = models.CharField(max_length=255, verbose_name='服务器地址', help_text='PVE服务器IP或域名，如：192.168.1.100')
    port = models.IntegerField(default=8006, verbose_name='端口', help_text='PVE API端口，默认8006')
    username = models.CharField(max_length=100, verbose_name='用户名', help_text='PVE登录用户名')
    password = models.CharField(max_length=255, verbose_name='密码', help_text='PVE登录密码（建议使用API Token）')
    token_id = models.CharField(max_length=100, blank=True, default='', verbose_name='Token ID', help_text='API Token ID（如果使用Token认证）')
    token_secret = models.CharField(max_length=255, blank=True, default='', verbose_name='Token Secret', help_text='API Token Secret（如果使用Token认证）')
    use_token = models.BooleanField(default=False, verbose_name='使用Token认证', help_text='是否使用Token认证而不是用户名密码')
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
