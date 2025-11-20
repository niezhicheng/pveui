import request from '@/utils/request'

export function getSessions(params) {
  return request({
    url: '/api/customer-service/sessions/',
    method: 'get',
    params,
  })
}

export function assignSession(id) {
  return request({
    url: `/api/customer-service/sessions/${id}/assign/`,
    method: 'post',
  })
}

export function closeSession(id) {
  return request({
    url: `/api/customer-service/sessions/${id}/close/`,
    method: 'post',
  })
}

export function sendAgentMessage(id, data) {
  return request({
    url: `/api/customer-service/sessions/${id}/send_message/`,
    method: 'post',
    data,
  })
}

export function getSessionMessages(params) {
  return request({
    url: '/api/customer-service/messages/',
    method: 'get',
    params,
  })
}

