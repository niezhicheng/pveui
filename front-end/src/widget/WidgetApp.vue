<template>
  <div class="cs-widget" :class="config.position" :style="{ '--theme-color': config.theme }">
    <div v-if="!open" class="cs-entry" :style="{ backgroundColor: config.theme }" @click="open = true">
      <span>客服</span>
    </div>
    <div v-else class="cs-panel">
      <div class="panel-header" :style="{ backgroundColor: config.theme }">
        <span>在线客服</span>
        <button class="close-btn" @click="open = false">×</button>
      </div>
      <div class="panel-body">
        <div class="message-list" ref="messageListEl">
          <div v-for="message in messages" :key="message.id" :class="['guest-message', message.sender_type]">
            <div class="sender">{{ senderLabel(message) }}</div>
            <div class="bubble">{{ message.content }}</div>
            <div class="time">{{ formatDate(message.created_at) }}</div>
          </div>
        </div>
        <div class="panel-input">
          <textarea v-model="input" placeholder="请输入内容..." @keydown.ctrl.enter.prevent="handleSend" />
          <button :disabled="sending" @click="handleSend">发送</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, onBeforeUnmount } from 'vue'
import { initGuestSession, sendGuestMessage, fetchGuestHistory, buildGuestWsUrl } from './api'

const props = defineProps({
  config: {
    type: Object,
    default: () => ({
      appId: 'default',
      theme: '#165dff',
      position: 'right',
    }),
  },
})

const open = ref(false)
const sessionId = ref('')
const secretToken = ref('')
const messages = ref([])
const input = ref('')
const sending = ref(false)
const messageListEl = ref(null)
const wsRef = ref(null)
let reconnectTimer = null

const getStorageKey = () => `cs-widget-session-${props.config.appId}`

const saveSession = () => {
  if (!sessionId.value || !secretToken.value) return
  localStorage.setItem(getStorageKey(), JSON.stringify({
    session_id: sessionId.value,
    secret_token: secretToken.value,
  }))
}

const loadSession = () => {
  const cached = localStorage.getItem(getStorageKey())
  if (cached) {
    try {
      const data = JSON.parse(cached)
      sessionId.value = data.session_id
      secretToken.value = data.secret_token
      return true
    } catch (e) {}
  }
  return false
}

const scrollToBottom = () => {
  const el = messageListEl.value
  if (!el) return
  el.scrollTop = el.scrollHeight
}

const formatDate = (value) => {
  if (!value) return ''
  const date = new Date(value)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

const senderLabel = (message) => {
  if (message.sender_type === 'agent') return '客服'
  if (message.sender_type === 'system') return '系统'
  return '我'
}

const ensureSession = async () => {
  if (sessionId.value && secretToken.value) return
  try {
    const res = await initGuestSession({
      app_id: props.config.appId,
      visitor_id: '',
      nickname: '',
      metadata: {
        referrer: document.referrer,
        location: window.location.href,
      },
    })
    sessionId.value = res.session_id
    secretToken.value = res.secret_token
    saveSession()
    connectWebSocket()
  } catch (e) {
    console.error('初始化会话失败', e)
  }
}

const loadHistory = async () => {
  if (!sessionId.value || !secretToken.value) return
  try {
    const res = await fetchGuestHistory({
      session_id: sessionId.value,
      secret_token: secretToken.value,
    })
    messages.value = Array.isArray(res) ? res : res.data || []
    await nextTick()
    scrollToBottom()
  } catch (e) {
    console.error('读取历史失败', e)
  }
}

const upsertMessage = (msg) => {
  const idx = messages.value.findIndex((m) => m.id === msg.id)
  if (idx >= 0) {
    messages.value[idx] = msg
  } else {
    messages.value.push(msg)
  }
  nextTick(scrollToBottom)
}

const handleSend = async () => {
  const content = input.value.trim()
  if (!content) return
  if (!sessionId.value || !secretToken.value) {
    await ensureSession()
  }
  sending.value = true
  try {
    const res = await sendGuestMessage({
      session_id: sessionId.value,
      secret_token: secretToken.value,
      content,
      message_type: 'text',
    })
    input.value = ''
    if (!wsRef.value || wsRef.value.readyState !== WebSocket.OPEN) {
      upsertMessage(res)
    }
  } catch (e) {
    console.error('发送失败', e)
  } finally {
    sending.value = false
  }
}

const connectWebSocket = () => {
  if (!sessionId.value || !secretToken.value) return
  if (wsRef.value) {
    wsRef.value.close()
    wsRef.value = null
  }
  const url = buildGuestWsUrl(sessionId.value, secretToken.value)
  const ws = new WebSocket(url)
  ws.onopen = () => {
    ws.send(JSON.stringify({ type: 'ping' }))
  }
  ws.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data)
      if (payload.type === 'message' && payload.data) {
        upsertMessage(payload.data)
      }
    } catch (e) {
      console.error('WS message parse error', e)
    }
  }
  ws.onclose = () => {
    wsRef.value = null
    if (reconnectTimer) clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(() => {
      if (sessionId.value && secretToken.value) {
        connectWebSocket()
      }
    }, 3000)
  }
  ws.onerror = () => {
    ws.close()
  }
  wsRef.value = ws
}

watch(open, (value) => {
  if (value && sessionId.value && secretToken.value) {
    loadHistory()
  }
})

watch(
  () => [sessionId.value, secretToken.value],
  ([sid, token]) => {
    if (sid && token) {
      connectWebSocket()
    }
  },
)

onMounted(async () => {
  const hasSession = loadSession()
  await ensureSession()
  if (hasSession) {
    await loadHistory()
  }
})

onBeforeUnmount(() => {
  if (wsRef.value) {
    wsRef.value.close()
    wsRef.value = null
  }
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
  }
})
</script>

<style scoped>
.cs-widget {
  position: fixed;
  bottom: 24px;
  z-index: 9999;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.cs-widget.right {
  right: 24px;
}

.cs-widget.left {
  left: 24px;
}

.cs-entry {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  cursor: pointer;
}

.cs-panel {
  width: 320px;
  height: 460px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  background: #fff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 12px 16px;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.close-btn {
  background: transparent;
  border: none;
  color: #fff;
  font-size: 18px;
  cursor: pointer;
}

.panel-body {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  background: #f6f6f6;
}

.guest-message {
  margin-bottom: 12px;
}

.guest-message .sender {
  font-size: 12px;
  color: #999;
}

.guest-message .bubble {
  display: inline-block;
  margin-top: 4px;
  padding: 8px 12px;
  border-radius: 8px;
  background: #fff;
  max-width: 80%;
  word-break: break-word;
}

.guest-message.guest {
  text-align: right;
}
.guest-message.guest .bubble {
  background: var(--theme-color, #165dff);
  color: #fff;
}

.guest-message.agent {
  text-align: left;
}

.guest-message .time {
  font-size: 12px;
  color: #bbb;
}

.panel-input {
  border-top: 1px solid #eee;
  padding: 8px;
  background: #fff;
}

.panel-input textarea {
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 8px;
  resize: none;
}

.panel-input button {
  margin-top: 8px;
  width: 100%;
  background: var(--theme-color, #165dff);
  border: none;
  color: #fff;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
}
</style>

