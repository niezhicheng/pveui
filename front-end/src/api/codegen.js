import request from '@/utils/request'

export function submitCodegen(data) {
  return request({ url: '/api/codegen/generate/', method: 'post', data })
}

