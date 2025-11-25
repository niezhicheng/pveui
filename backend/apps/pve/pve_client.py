"""PVE API客户端：封装Proxmox VE API调用。"""

import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin
import json
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class PVEAPIClient:
    """PVE API客户端类。"""
    
    def __init__(self, host: str, port: int = 8006, username: str = None, 
                 password: str = None, token_id: str = None, 
                 token_secret: str = None, use_token: bool = False,
                 verify_ssl: bool = False):
        """
        初始化PVE API客户端。
        
        Args:
            host: PVE服务器地址
            port: PVE API端口，默认8006
            username: 用户名（使用密码认证时）
            password: 密码（使用密码认证时）
            token_id: Token ID（使用Token认证时）
            token_secret: Token Secret（使用Token认证时）
            use_token: 是否使用Token认证
            verify_ssl: 是否验证SSL证书
        """
        self.host = host
        self.port = port
        self.base_url = f"https://{host}:{port}/api2/json"
        self.verify_ssl = verify_ssl
        self.use_token = use_token
        
        if use_token and token_id and token_secret:
            # 使用Token认证
            self.auth_header = {
                'Authorization': f'PVEAPIToken={token_id}={token_secret}'
            }
            self.auth = None
        else:
            # 使用用户名密码认证
            self.auth = HTTPBasicAuth(username, password)
            self.auth_header = {}
        
        self.session = requests.Session()
        if self.auth:
            self.session.auth = self.auth
        if self.auth_header:
            self.session.headers.update(self.auth_header)
        self.session.verify = verify_ssl
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """
        发送API请求。
        
        Args:
            method: HTTP方法（GET, POST, PUT, DELETE）
            endpoint: API端点
            params: URL参数
            data: 请求体数据
            
        Returns:
            API响应数据
            
        Raises:
            Exception: API请求失败时抛出异常
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = self.session.put(url, params=params, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params, timeout=30)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            result = response.json()
            
            # PVE API返回格式: {"data": {...}}
            if 'data' in result:
                return result['data']
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"PVE API请求失败: {method} {url}, 错误: {str(e)}")
            raise Exception(f"PVE API请求失败: {str(e)}")
    
    def get_version(self) -> Dict:
        """获取PVE版本信息。"""
        return self._request('GET', '/version')
    
    def get_nodes(self) -> dict:
        """获取所有节点列表。"""
        return self._request('GET', '/nodes')
    
    def get_node_status(self, node: str) -> Dict:
        """获取节点状态。"""
        return self._request('GET', f'/nodes/{node}/status')
    
    def get_vms(self, node: str) -> dict:
        """获取节点上的所有虚拟机。"""
        return self._request('GET', f'/nodes/{node}/qemu')
    
    def get_vm_status(self, node: str, vmid: int) -> Dict:
        """获取虚拟机状态。"""
        return self._request('GET', f'/nodes/{node}/qemu/{vmid}/status/current')
    
    def get_vm_config(self, node: str, vmid: int) -> Dict:
        """获取虚拟机配置。"""
        return self._request('GET', f'/nodes/{node}/qemu/{vmid}/config')
    
    def create_vm(self, node: str, vmid: int, config: Dict) -> dict:
        """
        创建虚拟机。
        
        Args:
            node: 节点名称
            vmid: 虚拟机ID
            config: 虚拟机配置字典
            
        Returns:
            UPID（任务ID）
        """
        # 创建虚拟机
        params = {'vmid': vmid}
        params.update(config)
        result = self._request('POST', f'/nodes/{node}/qemu', params=params)
        return result
    
    def clone_vm(self, node: str, newid: int, source_vmid: int, 
                 name: str = None, full: bool = False) -> str:
        """
        克隆虚拟机。
        
        Args:
            node: 节点名称
            newid: 新虚拟机ID
            source_vmid: 源虚拟机ID
            name: 新虚拟机名称
            full: 是否完整克隆
            
        Returns:
            UPID（任务ID）
        """
        params = {
            'newid': newid,
            'full': 1 if full else 0
        }
        if name:
            params['name'] = name
        
        result = self._request('POST', f'/nodes/{node}/qemu/{source_vmid}/clone', params=params)
        return result
    
    def start_vm(self, node: str, vmid: int) -> str:
        """启动虚拟机。"""
        return self._request('POST', f'/nodes/{node}/qemu/{vmid}/status/start')
    
    def stop_vm(self, node: str, vmid: int) -> str:
        """停止虚拟机。"""
        return self._request('POST', f'/nodes/{node}/qemu/{vmid}/status/stop')
    
    def shutdown_vm(self, node: str, vmid: int) -> str:
        """关闭虚拟机（优雅关闭）。"""
        return self._request('POST', f'/nodes/{node}/qemu/{vmid}/status/shutdown')
    
    def reboot_vm(self, node: str, vmid: int) -> str:
        """重启虚拟机。"""
        return self._request('POST', f'/nodes/{node}/qemu/{vmid}/status/reboot')
    
    def delete_vm(self, node: str, vmid: int) -> str:
        """删除虚拟机。"""
        return self._request('DELETE', f'/nodes/{node}/qemu/{vmid}')
    
    def get_storage(self, node: str) -> List[Dict]:
        """获取存储列表。"""
        return self._request('GET', f'/nodes/{node}/storage')
    
    def get_network(self, node: str) -> List[Dict]:
        """获取网络接口列表。"""
        return self._request('GET', f'/nodes/{node}/network')
    
    def get_task_status(self, node: str, upid: str) -> Dict:
        """获取任务状态。"""
        return self._request('GET', f'/nodes/{node}/tasks/{upid}/status')

