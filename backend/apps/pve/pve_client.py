"""PVE API客户端：封装Proxmox VE API调用。"""

import requests
from typing import Dict, List, Optional, Any, Union
import logging

logger = logging.getLogger(__name__)


class PVEAPIClient:
    """PVE API客户端类。"""
    
    def __init__(self, host: str, port: int = 8006, token_id: str = None, 
                 token_secret: str = None, verify_ssl: bool = False):
        """
        初始化PVE API客户端。
        
        Args:
            host: PVE服务器地址
            port: PVE API端口，默认8006
            token_id: Token ID
            token_secret: Token Secret
            verify_ssl: 是否验证SSL证书
        """
        self.host = host
        self.port = port
        self.base_url = f"https://{host}:{port}/api2/json"
        self.verify_ssl = verify_ssl
        
        if not token_id or not token_secret:
            raise ValueError("Token ID 和 Token Secret 是必需的")
        
        # 使用Token认证
        self.auth_header = {
            'Authorization': f'PVEAPIToken={token_id}={token_secret}'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.auth_header)
        self.session.verify = verify_ssl
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Union[Dict, List]:
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
        # 确保endpoint以/开头，然后直接拼接（不使用urljoin，避免路径被替换）
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        url = self.base_url.rstrip('/') + endpoint
        
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
            
            # 检查HTTP状态码
            if response.status_code >= 400:
                # 尝试解析错误信息
                try:
                    error_data = response.json()
                    # PVE API错误格式可能是 {"errors": {"param": "error message"}} 或 {"data": null, "errors": {...}}
                    if 'errors' in error_data:
                        errors = error_data['errors']
                        if isinstance(errors, dict):
                            # 提取所有错误信息
                            error_messages = []
                            for key, value in errors.items():
                                if isinstance(value, dict) and 'message' in value:
                                    error_messages.append(f"{key}: {value['message']}")
                                elif isinstance(value, str):
                                    error_messages.append(f"{key}: {value}")
                                else:
                                    error_messages.append(f"{key}: {str(value)}")
                            error_msg = '\n'.join(error_messages) if error_messages else str(errors)
                        else:
                            error_msg = str(errors)
                    else:
                        error_msg = error_data.get('message', '') or response.text
                except:
                    error_msg = response.text or f"HTTP {response.status_code}"
                raise Exception(f"PVE API错误 ({response.status_code}): {error_msg}")
            
            result = response.json()
            
            # PVE API返回格式: {"data": {...}}
            if 'data' in result:
                return result['data']
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('errors', {}).get('message', '') or error_data.get('message', '') or e.response.text
                except:
                    error_msg = e.response.text or str(e)
            logger.error(f"PVE API请求失败: {method} {url}, 错误: {error_msg}")
            raise Exception(f"PVE API请求失败: {error_msg}")
    
    def get_version(self) -> Dict:
        """获取PVE版本信息。"""
        return self._request('GET', '/version')
    
    def get_nodes(self) -> List[Dict]:
        """获取所有节点列表。"""
        result = self._request('GET', '/nodes')
        return result if isinstance(result, list) else [result]
    
    def get_node_status(self, node: str) -> Dict:
        """获取节点状态。"""
        result = self._request('GET', f'/nodes/{node}/status')
        return result if isinstance(result, dict) else {}
    
    def get_node_rrddata(
        self,
        node: str,
        timeframe: str = 'hour',
        cf: str = 'AVERAGE',
        datasource: Optional[str] = None
    ) -> List[Dict]:
        """
        获取节点的RRD监控数据。
        
        Args:
            node: 节点名称
            timeframe: 时间范围（hour、day、week、month、year）
            cf: 聚合方式（AVERAGE、MAX、MIN）
            datasource: 可选的数据源（如cpu、mem等），如果为空则返回全部
        """
        params = {
            'timeframe': timeframe or 'hour'
        }
        if cf:
            params['cf'] = cf
        if datasource:
            params['ds'] = datasource
        result = self._request('GET', f'/nodes/{node}/rrddata', params=params)
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return [result]
        return []
    
    def get_vms(self, node: str) -> List[Dict]:
        """获取节点上的所有虚拟机。"""
        result = self._request('GET', f'/nodes/{node}/qemu')
        return result if isinstance(result, list) else [result]
    
    def get_vm_status(self, node: str, vmid: int) -> Dict:
        """获取虚拟机状态。"""
        return self._request('GET', f'/nodes/{node}/qemu/{vmid}/status/current')
    
    def get_vm_config(self, node: str, vmid: int) -> Dict:
        """获取虚拟机配置。"""
        return self._request('GET', f'/nodes/{node}/qemu/{vmid}/config')
    
    def create_vnc_proxy(self, node: str, vmid: int, websocket: bool = True, generate_password: bool = True) -> Dict:
        """
        创建VNC代理会话，用于noVNC连接。
        """
        params = {
            'websocket': 1 if websocket else 0,
            'generate-password': 1 if generate_password else 0
        }
        return self._request('POST', f'/nodes/{node}/qemu/{vmid}/vncproxy', params=params)
    
    def update_vm_config(self, node: str, vmid: int, params: Dict) -> Dict:
        """
        更新虚拟机硬件配置。
        
        Args:
            node: 节点名称
            vmid: 虚拟机ID
            params: 需要更新的配置参数
        """
        if not params:
            raise ValueError("params 不能为空")
        return self._request('POST', f'/nodes/{node}/qemu/{vmid}/config', params=params)
    
    def create_vm(self, node: str, vmid: int, config: Dict) -> Dict:
        """
        创建虚拟机。
        
        Args:
            node: 节点名称
            vmid: 虚拟机ID（已经在config中，这里只是为了类型检查）
            config: 虚拟机配置字典，包含所有参数包括vmid
        
        Returns:
            UPID（任务ID）
        """
        # PVE API创建虚拟机使用URL参数（表单格式）
        # config已经包含了所有参数，包括vmid
        result = self._request('POST', f'/nodes/{node}/qemu', params=config)
        return result
    
    def clone_vm(
        self,
        node: str,
        newid: int,
        source_vmid: int,
        name: str = None,
        full: bool = False,
        target: str = None,
        storage: str = None,
        disk_format: str = None,
        description: str = None,
        pool: str = None,
        snapname: str = None
    ) -> Dict:
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
            'newid': newid
        }
        if full is not None:
            params['full'] = 1 if full else 0
        if name:
            params['name'] = name
        if target:
            params['target'] = target
        if storage:
            params['storage'] = storage
        if disk_format:
            params['format'] = disk_format
        if description:
            params['description'] = description
        if pool:
            params['pool'] = pool
        if snapname:
            params['snapname'] = snapname
        
        result = self._request('POST', f'/nodes/{node}/qemu/{source_vmid}/clone', params=params)
        return result
    
    def start_vm(self, node: str, vmid: int) -> Dict:
        """启动虚拟机。"""
        result = self._request('POST', f'/nodes/{node}/qemu/{vmid}/status/start')
        return result if isinstance(result, dict) else {}
    
    def stop_vm(self, node: str, vmid: int) -> Dict:
        """停止虚拟机。"""
        result = self._request('POST', f'/nodes/{node}/qemu/{vmid}/status/stop')
        return result if isinstance(result, dict) else {}
    
    def shutdown_vm(self, node: str, vmid: int) -> Dict:
        """关闭虚拟机（优雅关闭）。"""
        result = self._request('POST', f'/nodes/{node}/qemu/{vmid}/status/shutdown')
        return result if isinstance(result, dict) else {}
    
    def reboot_vm(self, node: str, vmid: int) -> Dict:
        """重启虚拟机。"""
        result = self._request('POST', f'/nodes/{node}/qemu/{vmid}/status/reboot')
        return result if isinstance(result, dict) else {}
    
    def delete_vm(self, node: str, vmid: int) -> Dict:
        """删除虚拟机。"""
        result = self._request('DELETE', f'/nodes/{node}/qemu/{vmid}')
        return result if isinstance(result, dict) else {}
    
    def get_storage(self, node: str) -> List[Dict]:
        """获取存储列表。"""
        result = self._request('GET', f'/nodes/{node}/storage')
        return result if isinstance(result, list) else [result] if result else []
    
    def get_network(self, node: str) -> List[Dict]:
        """获取网络接口列表。"""
        result = self._request('GET', f'/nodes/{node}/network')
        return result if isinstance(result, list) else [result] if result else []
    
    def get_task_status(self, node: str, upid: str) -> Dict:
        """获取任务状态。"""
        return self._request('GET', f'/nodes/{node}/tasks/{upid}/status')
    
    def get_storage_content(self, node: str, storage: str, content_type: str = None) -> List[Dict]:
        """
        获取存储内容。
        
        Args:
            node: 节点名称
            storage: 存储名称
            content_type: 内容类型（iso, vztmpl, images等），如果为None则返回所有类型
            
        Returns:
            存储内容列表
        """
        params = {}
        if content_type:
            params['content'] = content_type
        result = self._request('GET', f'/nodes/{node}/storage/{storage}/content', params=params)
        return result if isinstance(result, list) else [result] if result else []

    def upload_storage_content(
        self,
        node: str,
        storage: str,
        file_obj,
        filename: str,
        content: str = 'iso'
    ) -> Dict:
        """
        上传文件到指定存储。
        """
        if not file_obj:
            raise ValueError('缺少上传文件')
        if not filename:
            raise ValueError('缺少文件名')

        endpoint = f'/nodes/{node}/storage/{storage}/upload'
        url = self.base_url.rstrip('/') + endpoint
        data = {
            'content': content or 'iso',
            'filename': filename
        }
        if hasattr(file_obj, 'seek'):
            try:
                file_obj.seek(0)
            except Exception:
                pass

        files = {
            'filename': (filename, file_obj, 'application/octet-stream')
        }

        try:
            response = self.session.post(url, data=data, files=files, timeout=300)
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message') or response.text
                except Exception:
                    error_msg = response.text or f"HTTP {response.status_code}"
                raise Exception(f"PVE 上传失败 ({response.status_code}): {error_msg}")
            result = response.json()
            return result.get('data') if isinstance(result, dict) else result
        except requests.exceptions.RequestException as e:
            raise Exception(f"PVE 上传失败: {str(e)}")
    
    def get_next_vmid(self, vmid: int = None) -> int:
        """
        获取下一个可用的VMID。
        
        Args:
            vmid: 可选的VMID，用于检查该VMID是否可用（在检查时）
            
        Returns:
            下一个可用的VMID
        """
        params = {}
        if vmid:
            params['vmid'] = vmid
        result = self._request('GET', '/cluster/nextid', params=params)
        # PVE API返回格式可能是 {"data": 100} 或直接返回数字
        if isinstance(result, dict) and 'data' in result:
            return int(result['data'])
        elif isinstance(result, (int, str)):
            return int(result)
        else:
            # 如果API返回格式不符合预期，回退到默认值
            return 100

    def list_snapshots(self, node: str, vmid: int) -> List[Dict]:
        """获取虚拟机快照列表。"""
        result = self._request('GET', f'/nodes/{node}/qemu/{vmid}/snapshot')
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return [result]
        return []

    def create_snapshot(self, node: str, vmid: int, name: str, description: str = '', include_memory: bool = False) -> Dict:
        """创建虚拟机快照。"""
        params = {
            'snapname': name,
            'description': description or '',
            'vmstate': 1 if include_memory else 0
        }
        return self._request('POST', f'/nodes/{node}/qemu/{vmid}/snapshot', params=params)

    def rollback_snapshot(self, node: str, vmid: int, snapshot_name: str) -> Dict:
        """回滚到指定快照。"""
        return self._request('POST', f'/nodes/{node}/qemu/{vmid}/snapshot/{snapshot_name}/rollback')

    def delete_snapshot(self, node: str, vmid: int, snapshot_name: str) -> Dict:
        """删除指定快照。"""
        return self._request('DELETE', f'/nodes/{node}/qemu/{vmid}/snapshot/{snapshot_name}')

    def create_backup(self, node: str, vmid: int, storage: str, mode: str = 'snapshot',
                      compress: str = 'zstd', remove: bool = False, notes: str = '') -> Dict:
        """
        创建虚拟机备份（触发vzdump任务）。
        """
        params = {
            'vmid': vmid,
            'storage': storage,
            'mode': mode,
            'compress': compress,
            'remove': 1 if remove else 0
        }
        if notes:
            params['notes'] = notes
        return self._request('POST', f'/nodes/{node}/vzdump', params=params)

    def list_tasks(
        self,
        node: str,
        vmid: int = None,
        limit: int = 100,
        statusfilter: str = 'all'
    ) -> List[Dict]:
        """
        获取节点上的任务列表，可选过滤特定虚拟机。
        
        Args:
            node: 节点名称
            vmid: 可选，虚拟机ID（过滤该虚拟机相关任务）
            limit: 返回的任务数量限制
        """
        params = {
            'limit': limit
        }
        if statusfilter and statusfilter.lower() != 'all':
            params['statusfilter'] = statusfilter
        if vmid:
            params['vmid'] = vmid
        result = self._request('GET', f'/nodes/{node}/tasks', params=params)
        return result if isinstance(result, list) else [result] if result else []

    def get_task_log(self, node: str, upid: str, start: int = 0, limit: int = 50) -> List[str]:
        """
        获取任务日志。
        
        Args:
            node: 节点名称
            upid: 任务UPID
            start: 起始行号
            limit: 返回的日志行数
        """
        params = {
            'start': start,
            'limit': limit
        }
        result = self._request('GET', f'/nodes/{node}/tasks/{upid}/log', params=params)
        if isinstance(result, list):
            # PVE 返回格式：[{"n": 行号, "t": "日志内容"}, ...]
            return [item.get('t', '') for item in result if isinstance(item, dict)]
        return []

