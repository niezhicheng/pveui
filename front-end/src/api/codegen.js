import request from '@/utils/request'

export function submitCodegen(data) {
  return request({ url: '/api/codegen/generate/', method: 'post', data })
}

export function generateSchemaByAI(data) {
  return request({ url: '/api/codegen/ai-schema/', method: 'post', data })
}

