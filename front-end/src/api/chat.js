import request from '@/utils/request'

/**
 * 获取对话列表
 * @returns {Promise} 返回对话列表
 */
export function getConversations() {
  return request({
    url: '/api/chat/messages/conversations/',
    method: 'get'
  })
}

/**
 * 获取与指定用户的消息列表
 * @param {number} userId - 用户ID
 * @returns {Promise} 返回消息列表
 */
export function getMessagesWithUser(userId) {
  return request({
    url: '/api/chat/messages/with_user/',
    method: 'get',
    params: { user_id: userId }
  })
}

/**
 * 发送消息
 * @param {Object} data - { receiver: 用户ID, content: 消息内容 }
 * @returns {Promise}
 */
export function sendMessage(data) {
  return request({
    url: '/api/chat/messages/',
    method: 'post',
    data
  })
}

/**
 * 标记消息为已读
 * @param {number} messageId - 消息ID
 * @returns {Promise}
 */
export function markMessageRead(messageId) {
  return request({
    url: `/api/chat/messages/${messageId}/mark_read/`,
    method: 'post'
  })
}

/**
 * 标记与指定用户的所有消息为已读
 * @param {number} userId - 用户ID
 * @returns {Promise}
 */
export function markAllRead(userId) {
  return request({
    url: '/api/chat/messages/mark_all_read/',
    method: 'post',
    data: { user_id: userId }
  })
}

