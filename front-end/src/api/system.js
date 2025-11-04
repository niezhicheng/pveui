import request from '@/utils/request'

export function getSystemMetrics() {
  return request({ url: '/api/rbac/system/metrics/', method: 'get' })
}


