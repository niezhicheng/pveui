<template>
  <div class="chat-page">
    <a-card :bordered="false" style="height: calc(100vh - 120px); display: flex; flex-direction: column;">
      <template #title>
        <div style="display: flex; align-items: center; gap: 12px;">
          <a-typography-title :heading="4">员工聊天</a-typography-title>
          <a-tag :color="wsConnected ? 'green' : 'red'" size="small">
            {{ wsConnected ? '已连接' : '未连接' }}
          </a-tag>
        </div>
      </template>

      <div class="chat-container">
        <!-- 左侧：对话列表 -->
        <div class="chat-sidebar">
          <div class="sidebar-header">
            <a-input-search
              v-model="searchUser"
              placeholder="搜索用户"
              style="width: 100%"
              allow-clear
              @search="handleSearchUser"
            />
          </div>
          <div class="conversation-list">
            <div
              v-for="conv in filteredConversations"
              :key="conv.user_id"
              class="conversation-item"
              :class="{ active: currentUserId === conv.user_id }"
              @click="selectConversation(conv.user_id, conv.username)"
            >
              <div class="conversation-avatar">
                <a-avatar :size="40">{{ conv.username.charAt(0).toUpperCase() }}</a-avatar>
              </div>
              <div class="conversation-content">
                <div class="conversation-header">
                  <span class="conversation-name">{{ conv.username }}</span>
                  <span class="conversation-time" v-if="conv.last_message_time">
                    {{ formatTime(conv.last_message_time) }}
                  </span>
                </div>
                <div class="conversation-preview">
                  <span class="preview-text">{{ conv.last_message || '暂无消息' }}</span>
                  <a-badge
                    v-if="conv.unread_count > 0"
                    :count="conv.unread_count"
                    :number-style="{ backgroundColor: '#f53f3f' }"
                  />
                </div>
              </div>
            </div>
            <a-empty v-if="filteredConversations.length === 0" description="暂无对话" />
          </div>
        </div>

        <!-- 右侧：消息区域 -->
        <div class="chat-main">
          <div v-if="currentUserId" class="chat-messages">
            <div class="messages-header">
              <a-typography-title :heading="5">与 {{ currentUserName }} 的对话</a-typography-title>
              <a-button type="text" size="small" @click="markAllAsRead">
                标记全部已读
              </a-button>
            </div>
            <div class="messages-list" ref="messagesListRef">
              <div
                v-for="msg in messages"
                :key="msg.id"
                class="message-item"
                :class="{ 'message-sent': msg.sender_id === currentUser.id, 'message-received': msg.receiver_id === currentUser.id }"
              >
                <div class="message-avatar">
                  <a-avatar :size="32">
                    {{ (msg.sender_id === currentUser.id ? currentUser.username : currentUserName).charAt(0).toUpperCase() }}
                  </a-avatar>
                </div>
                <div class="message-content">
                  <div class="message-header">
                    <span class="message-sender">{{ msg.sender_id === currentUser.id ? '我' : msg.sender_username }}</span>
                    <span class="message-time">{{ formatDateTime(msg.created_at) }}</span>
                  </div>
                  <div class="message-text">{{ msg.content }}</div>
                </div>
              </div>
              <div v-if="messages.length === 0" class="empty-messages">
                <a-empty description="暂无消息，开始聊天吧~" />
              </div>
            </div>
            <div class="messages-input">
              <a-textarea
                v-model="newMessage"
                placeholder="输入消息..."
                :auto-size="{ minRows: 2, maxRows: 5 }"
                @keydown.ctrl.enter="handleSendMessage"
                @keydown.meta.enter="handleSendMessage"
              />
              <div class="input-actions">
                <a-space>
                  <a-button type="primary" :loading="sending" @click="handleSendMessage">
                    发送 (Ctrl+Enter)
                  </a-button>
                </a-space>
              </div>
            </div>
          </div>
          <div v-else class="chat-placeholder">
            <a-empty description="请从左侧选择一个对话" />
          </div>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getConversations, getMessagesWithUser, sendMessage, markAllRead } from '@/api/chat'
import { getUserInfo } from '@/api/user'

const currentUser = ref({})
const conversations = ref([])
const searchUser = ref('')
const currentUserId = ref(null)
const currentUserName = ref('')
const messages = ref([])
const newMessage = ref('')
const sending = ref(false)
const messagesListRef = ref(null)
const wsConnected = ref(false)
let ws = null
let pingTimer = null

// 过滤后的对话列表
const filteredConversations = computed(() => {
  if (!searchUser.value) {
    return conversations.value
  }
  const keyword = searchUser.value.toLowerCase()
  return conversations.value.filter(conv => 
    conv.username.toLowerCase().includes(keyword)
  )
})

// 获取当前用户信息
const loadCurrentUser = async () => {
  try {
    const userInfo = await getUserInfo()
    currentUser.value = userInfo
  } catch (e) {
    console.error('获取用户信息失败:', e)
  }
}

// 加载对话列表
const loadConversations = async () => {
  try {
    const data = await getConversations()
    conversations.value = data
  } catch (e) {
    console.error('加载对话列表失败:', e)
    Message.error('加载对话列表失败')
  }
}

// 选择对话
const selectConversation = async (userId, username) => {
  currentUserId.value = userId
  currentUserName.value = username
  await loadMessages(userId)
  // 标记为已读
  try {
    await markAllRead(userId)
    // 更新本地未读数
    const conv = conversations.value.find(c => c.user_id === userId)
    if (conv) {
      conv.unread_count = 0
    }
  } catch (e) {
    console.error('标记已读失败:', e)
  }
}

// 加载消息
const loadMessages = async (userId) => {
  try {
    const data = await getMessagesWithUser(userId)
    messages.value = data
    // 滚动到底部
    await nextTick()
    scrollToBottom()
  } catch (e) {
    console.error('加载消息失败:', e)
    Message.error('加载消息失败')
  }
}

// 发送消息
const handleSendMessage = async () => {
  if (!newMessage.value.trim()) {
    return
  }
  if (!currentUserId.value) {
    Message.warning('请先选择一个对话')
    return
  }
  
  sending.value = true
  try {
    await sendMessage({
      receiver: currentUserId.value,
      content: newMessage.value.trim()
    })
    newMessage.value = ''
    // WebSocket会实时推送消息，不需要重新加载
    // 但如果WebSocket未连接，则回退到轮询
    if (!wsConnected.value) {
      await loadMessages(currentUserId.value)
      await loadConversations()
    }
  } catch (e) {
    console.error('发送消息失败:', e)
    Message.error('发送消息失败')
  } finally {
    sending.value = false
  }
}

// 标记全部已读
const markAllAsRead = async () => {
  if (!currentUserId.value) return
  try {
    await markAllRead(currentUserId.value)
    const conv = conversations.value.find(c => c.user_id === currentUserId.value)
    if (conv) {
      conv.unread_count = 0
    }
    Message.success('已标记为已读')
  } catch (e) {
    console.error('标记已读失败:', e)
    Message.error('标记已读失败')
  }
}

// 搜索用户
const handleSearchUser = () => {
  // 搜索逻辑已在 computed 中处理
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesListRef.value) {
    messagesListRef.value.scrollTop = messagesListRef.value.scrollHeight
  }
}

// 格式化时间（相对时间）
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString()
}

// 格式化日期时间
const formatDateTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const msgDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  
  if (msgDate.getTime() === today.getTime()) {
    // 今天，只显示时间
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else {
    // 其他日期，显示日期和时间
    return date.toLocaleString('zh-CN', { 
      month: '2-digit', 
      day: '2-digit', 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }
}

// WebSocket连接
const connectWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  let host = import.meta.env.VITE_HOST || 'http://127.0.0.1:8000'
  // 移除协议前缀
  host = host.replace(/^https?:\/\//, '')
  const wsPath = `${protocol}//${host}/ws/chat/`
  
  console.log('连接WebSocket:', wsPath)
  
  try {
    ws = new WebSocket(wsPath)
    
    ws.onopen = () => {
      console.log('WebSocket连接已建立')
      wsConnected.value = true
      // 开始心跳检测
      startPing()
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleWebSocketMessage(data)
      } catch (e) {
        console.error('解析WebSocket消息失败:', e)
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
      wsConnected.value = false
    }
    
    ws.onclose = () => {
      console.log('WebSocket连接已关闭')
      wsConnected.value = false
      stopPing()
      // 尝试重连（5秒后）
      setTimeout(() => {
        if (currentUser.value.id) {
          connectWebSocket()
        }
      }, 5000)
    }
  } catch (e) {
    console.error('WebSocket连接失败:', e)
    wsConnected.value = false
  }
}

// 处理WebSocket消息
const handleWebSocketMessage = (data) => {
  if (data.type === 'pong') {
    // 心跳响应
    return
  }
  
  if (data.type === 'new_message' || data.type === 'message_sent') {
    // 收到新消息
    const messageData = data.data
    
    // 如果是当前对话的消息，添加到消息列表
    if (currentUserId.value && 
        (messageData.receiver_id === currentUserId.value || 
         messageData.sender_id === currentUserId.value)) {
      // 检查消息是否已存在
      const exists = messages.value.some(m => m.id === messageData.id)
      if (!exists) {
        messages.value.push(messageData)
        nextTick(() => {
          scrollToBottom()
        })
      }
    }
    
    // 更新对话列表
    updateConversationFromMessage(messageData)
  }
  
  if (data.type === 'unread_update') {
    // 未读数更新
    const conv = conversations.value.find(c => c.user_id === data.user_id)
    if (conv) {
      conv.unread_count = data.unread_count
    }
  }
}

// 从消息更新对话列表
const updateConversationFromMessage = (messageData) => {
  const otherUserId = messageData.sender_id === currentUser.value.id 
    ? messageData.receiver_id 
    : messageData.sender_id
  
  let conv = conversations.value.find(c => c.user_id === otherUserId)
  
  if (conv) {
    // 更新现有对话
    conv.last_message = messageData.content
    conv.last_message_time = messageData.created_at
    if (messageData.receiver_id === currentUser.value.id) {
      // 如果是接收的消息，增加未读数（如果不在当前对话中）
      if (currentUserId.value !== otherUserId) {
        conv.unread_count = (conv.unread_count || 0) + 1
      }
    }
  } else {
    // 创建新对话
    const otherUser = messageData.sender_id === currentUser.value.id
      ? { id: messageData.receiver_id, username: messageData.receiver_username }
      : { id: messageData.sender_id, username: messageData.sender_username }
    
    conversations.value.unshift({
      user_id: otherUser.id,
      username: otherUser.username,
      last_message: messageData.content,
      last_message_time: messageData.created_at,
      unread_count: messageData.receiver_id === currentUser.value.id ? 1 : 0,
    })
  }
  
  // 按时间排序
  conversations.value.sort((a, b) => {
    const timeA = a.last_message_time ? new Date(a.last_message_time).getTime() : 0
    const timeB = b.last_message_time ? new Date(b.last_message_time).getTime() : 0
    return timeB - timeA
  })
}

// 心跳检测
const startPing = () => {
  pingTimer = setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }))
    }
  }, 30000) // 每30秒发送一次心跳
}

const stopPing = () => {
  if (pingTimer) {
    clearInterval(pingTimer)
    pingTimer = null
  }
}

// 断开WebSocket
const disconnectWebSocket = () => {
  if (ws) {
    ws.close()
    ws = null
  }
  stopPing()
  wsConnected.value = false
}

onMounted(async () => {
  await loadCurrentUser()
  await loadConversations()
  // 连接WebSocket
  connectWebSocket()
})

onUnmounted(() => {
  disconnectWebSocket()
})
</script>

<style scoped>
.chat-page {
  padding: 20px;
  height: 100%;
}

.chat-container {
  display: flex;
  height: calc(100vh - 200px);
  gap: 16px;
}

.chat-sidebar {
  width: 300px;
  border-right: 1px solid var(--color-border-2);
  display: flex;
  flex-direction: column;
  background: var(--color-bg-1);
}

.sidebar-header {
  padding: 12px;
  border-bottom: 1px solid var(--color-border-2);
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
}

.conversation-item {
  padding: 12px;
  cursor: pointer;
  display: flex;
  gap: 12px;
  border-bottom: 1px solid var(--color-border-2);
  transition: background-color 0.2s;
}

.conversation-item:hover {
  background: var(--color-bg-2);
}

.conversation-item.active {
  background: var(--color-primary-light-1);
}

.conversation-avatar {
  flex-shrink: 0;
}

.conversation-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.conversation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.conversation-name {
  font-weight: 500;
  color: var(--color-text-1);
}

.conversation-time {
  font-size: 12px;
  color: var(--color-text-3);
}

.conversation-preview {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.preview-text {
  font-size: 12px;
  color: var(--color-text-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-1);
}

.chat-messages {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.messages-header {
  padding: 16px;
  border-bottom: 1px solid var(--color-border-2);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.messages-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  gap: 12px;
  max-width: 70%;
}

.message-item.message-sent {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-item.message-received {
  align-self: flex-start;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-header {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 12px;
  color: var(--color-text-3);
}

.message-sender {
  font-weight: 500;
}

.message-time {
  color: var(--color-text-4);
}

.message-text {
  padding: 8px 12px;
  background: var(--color-bg-3);
  border-radius: 8px;
  word-wrap: break-word;
  line-height: 1.5;
}

.message-sent .message-text {
  background: var(--color-primary-light-1);
  color: var(--color-primary-6);
}

.empty-messages {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.messages-input {
  padding: 16px;
  border-top: 1px solid var(--color-border-2);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
}

.chat-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>

