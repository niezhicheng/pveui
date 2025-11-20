import request from '@/utils/request'

/**
 * 获取系统设置列表
 */
export function getSystemSettings(params) {
  return request({
    url: '/api/system/settings/',
    method: 'get',
    params
  })
}

/**
 * 获取系统设置详情
 */
export function getSystemSetting(id) {
  return request({
    url: `/api/system/settings/${id}/`,
    method: 'get'
  })
}

/**
 * 创建系统设置
 */
export function createSystemSetting(data) {
  return request({
    url: '/api/system/settings/',
    method: 'post',
    data
  })
}

/**
 * 更新系统设置
 */
export function updateSystemSetting(id, data) {
  return request({
    url: `/api/system/settings/${id}/`,
    method: 'patch',
    data
  })
}

/**
 * 删除系统设置
 */
export function deleteSystemSetting(id) {
  return request({
    url: `/api/system/settings/${id}/`,
    method: 'delete'
  })
}

/**
 * 按分类获取系统设置
 */
export function getSystemSettingsByCategory(category) {
  return request({
    url: '/api/system/settings/by_category/',
    method: 'get',
    params: { category }
  })
}

/**
 * 批量更新系统设置
 */
export function bulkUpdateSystemSettings(data) {
  return request({
    url: '/api/system/settings/bulk_update/',
    method: 'post',
    data
  })
}

/**
 * 根据 key 获取系统设置
 */
export function getSystemSettingByKey(key) {
  return request({
    url: '/api/system/settings/get_by_key/',
    method: 'get',
    params: { key }
  })
}

