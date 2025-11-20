import request from '@/utils/request'

export function getKnowledgeList(params) {
  return request({
    url: '/api/knowledge/articles/',
    method: 'get',
    params,
  })
}

export function getKnowledgeDetail(id) {
  return request({
    url: `/api/knowledge/articles/${id}/`,
    method: 'get',
  })
}

export function createKnowledge(data) {
  return request({
    url: '/api/knowledge/articles/',
    method: 'post',
    data,
  })
}

export function updateKnowledge(id, data) {
  return request({
    url: `/api/knowledge/articles/${id}/`,
    method: 'put',
    data,
  })
}

export function patchKnowledge(id, data) {
  return request({
    url: `/api/knowledge/articles/${id}/`,
    method: 'patch',
    data,
  })
}

export function deleteKnowledge(id) {
  return request({
    url: `/api/knowledge/articles/${id}/`,
    method: 'delete',
  })
}

export function getKnowledgeCategories() {
  return request({
    url: '/api/knowledge/articles/categories/',
    method: 'get',
  })
}


