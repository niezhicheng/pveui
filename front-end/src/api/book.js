import request from '@/utils/request'

export function getBookList(params) {
  return request({ url: `/api/book/book/`, method: 'get', params })
}

export function getBookDetail(id) {
  return request({ url: `/api/book/book/` + id + '/', method: 'get' })
}

export function createBook(data) {
  return request({ url: `/api/book/book/`, method: 'post', data })
}

export function updateBook(id, data) {
  return request({ url: `/api/book/book/` + id + '/', method: 'put', data })
}

export function deleteBook(id) {
  return request({ url: `/api/book/book/` + id + '/', method: 'delete' })
}

