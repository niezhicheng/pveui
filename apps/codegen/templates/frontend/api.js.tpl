import request from '@/utils/request'

export function get${ModelName}List(params) {
  return request({ url: `/api/${AppLabel}/${model_name}/`, method: 'get', params })
}

export function get${ModelName}Detail(id) {
  return request({ url: `/api/${AppLabel}/${model_name}/` + id + '/', method: 'get' })
}

export function create${ModelName}(data) {
  return request({ url: `/api/${AppLabel}/${model_name}/`, method: 'post', data })
}

export function update${ModelName}(id, data) {
  return request({ url: `/api/${AppLabel}/${model_name}/` + id + '/', method: 'put', data })
}

export function delete${ModelName}(id) {
  return request({ url: `/api/${AppLabel}/${model_name}/` + id + '/', method: 'delete' })
}

