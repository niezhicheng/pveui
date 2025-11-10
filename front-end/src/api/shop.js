import request from '@/utils/request'

/**
 * 获取商品列表
 */
export function getProducts() {
  return request({
    url: '/api/shop/products/',
    method: 'get'
  })
}

/**
 * 创建订单
 * @param {Object} data - { product_id, quantity, contact, remark }
 */
export function createOrder(data) {
  return request({
    url: '/api/shop/orders/',
    method: 'post',
    data
  })
}

/**
 * 查询订单
 * @param {String} orderNo - 订单号
 */
export function getOrder(orderNo) {
  return request({
    url: `/api/shop/orders/${orderNo}/`,
    method: 'get'
  })
}

