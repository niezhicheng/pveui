import request from '@/utils/request'

/**
 * PVE服务器相关API
 */

/**
 * 获取PVE服务器列表
 */
export function getPVEServers(params) {
  return request({
    url: '/api/pve/servers/',
    method: 'get',
    params
  })
}

/**
 * 获取PVE服务器详情
 */
export function getPVEServer(id) {
  return request({
    url: `/api/pve/servers/${id}/`,
    method: 'get'
  })
}

/**
 * 创建PVE服务器
 */
export function createPVEServer(data) {
  return request({
    url: '/api/pve/servers/',
    method: 'post',
    data
  })
}

/**
 * 更新PVE服务器
 */
export function updatePVEServer(id, data) {
  return request({
    url: `/api/pve/servers/${id}/`,
    method: 'patch',
    data
  })
}

/**
 * 删除PVE服务器
 */
export function deletePVEServer(id) {
  return request({
    url: `/api/pve/servers/${id}/`,
    method: 'delete'
  })
}

/**
 * 测试PVE服务器连接
 */
export function testPVEServerConnection(id) {
  return request({
    url: `/api/pve/servers/${id}/test_connection/`,
    method: 'post'
  })
}

/**
 * 获取PVE服务器节点列表
 */
export function getPVEServerNodes(id) {
  return request({
    url: `/api/pve/servers/${id}/nodes/`,
    method: 'get'
  })
}

/**
 * 获取节点上的虚拟机列表
 */
export function getNodeVMs(serverId, node) {
  return request({
    url: `/api/pve/servers/${serverId}/nodes/${node}/vms/`,
    method: 'get'
  })
}

/**
 * 获取节点存储列表
 */
export function getNodeStorage(serverId, node) {
  return request({
    url: `/api/pve/servers/${serverId}/nodes/${node}/storage/`,
    method: 'get'
  })
}

/**
 * 获取存储内容列表（按类型可选）
 */
export function getStorageContent(serverId, node, storage, params) {
  return request({
    url: `/api/pve/servers/${serverId}/nodes/${node}/storage/${storage}/content/`,
    method: 'get',
    params
  })
}

/**
 * 上传文件到存储
 */
export function uploadStorageContent(serverId, node, storage, data) {
  return request({
    url: `/api/pve/servers/${serverId}/nodes/${node}/storage/${storage}/upload/`,
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * 获取存储中的ISO镜像列表（兼容旧接口）
 */
export function getStorageISO(serverId, node, storage) {
  return getStorageContent(serverId, node, storage, { content: 'iso' })
}

/**
 * 获取节点网络接口列表
 */
export function getNodeNetwork(serverId, node) {
  return request({
    url: `/api/pve/servers/${serverId}/nodes/${node}/network/`,
    method: 'get'
  })
}

/**
 * 获取节点监控数据
 */
export function getNodeMonitor(serverId, node, params) {
  return request({
    url: `/api/pve/servers/${serverId}/nodes/${node}/monitor/`,
    method: 'get',
    params
  })
}

/**
 * 获取下一个可用的VMID
 */
export function getNextVMID(serverId) {
  return request({
    url: `/api/pve/servers/${serverId}/next-vmid/`,
    method: 'get'
  })
}

/**
 * 虚拟机相关API
 */

/**
 * 获取虚拟机列表
 */
export function getVirtualMachines(params) {
  return request({
    url: '/api/pve/virtual-machines/',
    method: 'get',
    params
  })
}

/**
 * 获取虚拟机详情
 */
export function getVirtualMachine(id) {
  return request({
    url: `/api/pve/virtual-machines/${id}/`,
    method: 'get'
  })
}

/**
 * 创建虚拟机
 */
export function createVirtualMachine(data) {
  return request({
    url: '/api/pve/virtual-machines/create_vm/',
    method: 'post',
    data
  })
}

/**
 * 删除虚拟机
 */
export function deleteVirtualMachine(id) {
  return request({
    url: `/api/pve/virtual-machines/${id}/`,
    method: 'delete'
  })
}

/**
 * 虚拟机操作（启动、停止、重启等）
 */
export function vmAction(id, action) {
  return request({
    url: `/api/pve/virtual-machines/${id}/vm_action/`,
    method: 'post',
    data: { action }
  })
}

/**
 * 同步虚拟机状态
 */
export function syncVMStatus(id) {
  return request({
    url: `/api/pve/virtual-machines/${id}/sync_status/`,
    method: 'get'
  })
}

/**
 * 更新虚拟机硬件配置
 */
export function updateVirtualMachineHardware(id, data) {
  return request({
    url: `/api/pve/virtual-machines/${id}/update-hardware/`,
    method: 'post',
    data
  })
}

export function getVMOptions(id) {
  return request({
    url: `/api/pve/virtual-machines/${id}/options/`,
    method: 'get'
  })
}

export function updateVMOptions(id, data) {
  return request({
    url: `/api/pve/virtual-machines/${id}/options/`,
    method: 'post',
    data
  })
}

/**
 * 创建虚拟机控制台会话 (noVNC)
 */
export function createVMConsoleSession(id, data) {
  return request({
    url: `/api/pve/virtual-machines/${id}/console-session/`,
    method: 'post',
    data
  })
}

export function getVMBackups(id) {
  return request({
    url: `/api/pve/virtual-machines/${id}/backups/`,
    method: 'get'
  })
}

export function createVMBackup(id, data) {
  return request({
    url: `/api/pve/virtual-machines/${id}/create_backup/`,
    method: 'post',
    data
  })
}

export function getVMSnapshots(id) {
  return request({
    url: `/api/pve/virtual-machines/${id}/snapshots/`,
    method: 'get'
  })
}

export function createVMSnapshot(id, data) {
  return request({
    url: `/api/pve/virtual-machines/${id}/create_snapshot/`,
    method: 'post',
    data
  })
}

export function rollbackVMSnapshot(id, data) {
  return request({
    url: `/api/pve/virtual-machines/${id}/rollback_snapshot/`,
    method: 'post',
    data
  })
}

export function deleteVMSnapshot(id, data) {
  return request({
    url: `/api/pve/virtual-machines/${id}/delete_snapshot/`,
    method: 'post',
    data
  })
}

export function cloneVirtualMachine(id, data) {
  return request({
    url: `/api/pve/virtual-machines/${id}/clone/`,
    method: 'post',
    data
  })
}

/**
 * 获取虚拟机任务历史
 */
export function getVMTasks(id, params) {
  return request({
    url: `/api/pve/virtual-machines/${id}/tasks/`,
    method: 'get',
    params
  })
}

/**
 * 获取任务日志
 */
export function getVMTaskLog(id, data) {
  return request({
    url: `/api/pve/virtual-machines/${id}/task-log/`,
    method: 'post',
    data
  })
}

