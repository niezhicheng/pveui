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

