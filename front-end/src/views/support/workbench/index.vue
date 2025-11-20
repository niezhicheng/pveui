<template>
  <div class="cs-workbench">
    <a-card class="session-card">
      <template #title>
        <div class="card-title">
          <a-typography-title :heading="5">访客会话</a-typography-title>
          <a-input-search
            v-model="sessionSearch"
            placeholder="搜索访客/来源"
            style="width: 200px"
            allow-clear
            @search="fetchSessions"
            @clear="fetchSessions"
          />
        </div>
      </template>
      <a-spin :loading="sessionsLoading">
        <div class="session-list">
          <div
            v-for="session in sessions"
            :key="session.id"
            class="session-item"
            :class="{ active: currentSession?.id === session.id }"
            @click="selectSession(session)"
          >
            <div class="session-header">
              <span class="session-name">{{ session.nickname }}</span>
              <a-tag size="small" :color="statusTagColor(session.status)">{{ statusText(session.status) }}</a-tag>
            </div>
            <div class="session-meta">
              <span>ID: {{ session.session_id.slice(0, 8) }}</span>
              <span v-if="session.assigned_to">客服: {{ session.assigned_to.username }}</span>
            </div>
            <div class="session-last">{{ session.last_message || '暂无消息' }}</div>
          </div>
        </div>
      </a-spin>
    </a-card>

    <a-card class="chat-card" v-if="currentSession">
      <template #title>
        <div class="card-title">
          <div>
            <a-typography-title :heading="5">{{ currentSession.nickname }}</a-typography-title>
            <div class="chat-meta">
              <span>会话ID：{{ currentSession.session_id }}</span>
              <span>状态：{{ statusText(currentSession.status) }}</span>
            </div>
          </div>
          <a-space>
            <a-button size="small" @click="handleAssign" v-if="currentSession.status !== 'closed'">接入会话</a-button>
            <a-button size="small" status="danger" @click="handleClose" v-if="currentSession.status !== 'closed'">
              结束会话
            </a-button>
          </a-space>
        </div>
      </template>

      <div class="chat-content" ref="messageContainer">
        <a-spin :loading="messagesLoading">
          <div v-for="message in messages" :key="message.id" class="message-item" :class="messageClass(message)">
            <div class="message-info">
              <span class="message-sender">{{ senderLabel(message) }}</span>
              <span class="message-time">{{ formatDate(message.created_at) }}</span>
            </div>
            <div class="message-bubble">
              <div v-if="message.message_type === 'text'">{{ message.content }}</div>
              <a-image
                v-else-if="message.message_type === 'image'"
                :src="message.metadata?.url || message.content"
                width="120"
              />
              <a-tag v-else>附件消息</a-tag>
            </div>
          </div>
        </a-spin>
      </div>

      <div class="chat-input">
        <a-textarea
          v-model="newMessage"
          placeholder="输入消息，按 Ctrl+Enter 发送"
          :auto-size="{ minRows: 2, maxRows: 4 }"
          @keydown.ctrl.enter.prevent="handleSend"
        />
        <div class="chat-actions">
          <a-space>
            <a-button type="primary" :loading="sending" @click="handleSend">发送</a-button>
          </a-space>
        </div>
      </div>
    </a-card>

    <a-card v-else class="chat-card">
      <a-empty description="请选择左侧会话" />
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import { Message } from '@arco-design/web-vue'
import dayjs from 'dayjs'
import {
  getSessions,
  assignSession,
  closeSession,
  getSessionMessages,
  sendAgentMessage,
} from '@/api/customer-service'

const sessionsLoading = ref(false)
const sessions = ref([])
const sessionSearch = ref('')
const currentSession = ref(null)

const messagesLoading = ref(false)
const messages = ref([])
const newMessage = ref('')
const sending = ref(false)

const messageContainer = ref(null)

const pagination = reactive({
  page: 1,
  pageSize: 20,
})

const fetchSessions = async () => {
  sessionsLoading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (sessionSearch.value) params.search = sessionSearch.value
    const res = await getSessions(params)
    const data = res.results || res.data?.results || res.data || []
    sessions.value = Array.isArray(data) ? data : []
    if (!currentSession.value && sessions.value.length > 0) {
      selectSession(sessions.value[0])
    }
  } catch (e) {
    Message.error('获取会话失败：' + (e.message || '未知错误'))
  } finally {
    sessionsLoading.value = false
  }
}

const fetchMessages = async () => {
  if (!currentSession.value) return
  messagesLoading.value = true
  try {
    const res = await getSessionMessages({ session_id: currentSession.value.session_id })
    messages.value = res.results || res.data?.results || res.data || []
    await nextTick()
    scrollToBottom()
  } catch (e) {
    Message.error('获取消息失败：' + (e.message || '未知错误'))
  } finally {
    messagesLoading.value = false
  }
}

const selectSession = (session) => {
  currentSession.value = session
  fetchMessages()
}

const handleAssign = async () => {
  if (!currentSession.value) return
  try {
    await assignSession(currentSession.value.id)
    Message.success('已接入会话')
    fetchSessions()
  } catch (e) {
    Message.error('接入失败：' + (e.message || '未知错误'))
  }
}

const handleClose = async () => {
  if (!currentSession.value) return
  try {
    await closeSession(currentSession.value.id)
    Message.success('会话已结束')
    fetchSessions()
  } catch (e) {
    Message.error('结束会话失败：' + (e.message || '未知错误'))
  }
}

const handleSend = async () => {
  if (!currentSession.value) return
  const content = newMessage.value.trim()
  if (!content) {
    Message.warning('请输入内容')
    return
  }
  sending.value = true
  try {
    await sendAgentMessage(currentSession.value.id, { content, message_type: 'text' })
    newMessage.value = ''
    fetchMessages()
    fetchSessions()
  } catch (e) {
    Message.error('发送失败：' + (e.message || '未知错误'))
  } finally {
    sending.value = false
  }
}

const senderLabel = (message) => {
  if (message.sender_type === 'agent') {
    return message.sender?.username || '客服'
  }
  if (message.sender_type === 'system') {
    return '系统'
  }
  return currentSession.value?.nickname || '访客'
}

const messageClass = (message) => {
  return {
    'from-agent': message.sender_type === 'agent',
    'from-guest': message.sender_type === 'guest',
    'from-system': message.sender_type === 'system',
  }
}

const statusText = (status) => {
  switch (status) {
    case 'pending':
      return '待接入'
    case 'active':
      return '会话中'
    case 'closed':
      return '已结束'
    default:
      return status
  }
}

const statusTagColor = (status) => {
  switch (status) {
    case 'pending':
      return 'orangered'
    case 'active':
      return 'green'
    case 'closed':
      return 'gray'
    default:
      return 'blue'
  }
}

const formatDate = (value) => {
  if (!value) return '-'
  return dayjs(value).format('MM-DD HH:mm')
}

const scrollToBottom = () => {
  const el = messageContainer.value
  if (!el) return
  el.scrollTop = el.scrollHeight
}

watch(
  messages,
  () => {
    nextTick(scrollToBottom)
  },
  { deep: true },
)

onMounted(() => {
  fetchSessions()
})
</script>

<style scoped>
.cs-workbench {
  display: flex;
  gap: 16px;
  height: calc(100vh - 120px);
}

.session-card {
  width: 320px;
  overflow: hidden;
}

.chat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-list {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.session-item {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
}

.session-item.active {
  background: #f5f7ff;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.session-name {
  font-weight: 600;
}

.session-meta {
  font-size: 12px;
  color: #86909c;
  display: flex;
  justify-content: space-between;
}

.session-last {
  font-size: 13px;
  color: #4e5969;
  margin-top: 4px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}

.chat-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #fafafa;
}

.message-item {
  margin-bottom: 16px;
}

.message-item.from-agent {
  text-align: right;
}

.message-item.from-system {
  text-align: center;
}

.message-info {
  font-size: 12px;
  color: #86909c;
}

.message-bubble {
  display: inline-block;
  padding: 8px 12px;
  border-radius: 8px;
  background: #fff;
  margin-top: 4px;
}

.message-item.from-agent .message-bubble {
  background: #165dff;
  color: #fff;
}

.chat-input {
  border-top: 1px solid #f0f0f0;
  padding: 12px 0;
}

.chat-actions {
  margin-top: 8px;
  text-align: right;
}

.chat-meta {
  font-size: 12px;
  color: #86909c;
}
</style>

