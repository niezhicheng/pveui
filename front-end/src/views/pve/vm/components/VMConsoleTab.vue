<template>
  <div class="vm-console-tab">
    <a-card :bordered="false">
      <a-alert type="info" show-icon style="margin-bottom: 12px;">
        <template #title>提示</template>
        控制台通过本系统代理访问 PVE，无需手动登录 PVE，但首次加载可能需要几秒钟。
      </a-alert>
      <div class="pve-console-wrapper">
        <div v-if="consoleLoading" class="novnc-placeholder">
          <a-spin />
          <p style="margin-top: 12px;">正在建立控制台会话...</p>
        </div>
        <div v-else-if="consoleError" class="novnc-placeholder">
          <p>{{ consoleError }}</p>
          <a-button type="text" @click="initConsole">重试</a-button>
        </div>
        <!-- noVNC 容器始终存在，通过样式控制显示 -->
        <div
          ref="novncContainer"
          :id="`noVNC_container_${vmId}`"
          class="novnc-container"
          :style="{ display: consoleLoading || consoleError ? 'none' : 'flex' }"
        ></div>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { createVMConsoleSession } from '@/api/pve'
import RFB from '@novnc/novnc/core/rfb'

const props = defineProps({
  vm: {
    type: Object,
    required: true
  },
  vmId: {
    type: [Number, String],
    required: true
  },
  active: {
    type: Boolean,
    default: false
  }
})

const novncContainer = ref(null)
const consoleLoading = ref(false)
const consoleError = ref('')
const rfb = ref(null)

const API_BASE = (import.meta.env.VITE_HOST || '').replace(/\/$/, '')

const buildBackendUrl = (path) => {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  const base = API_BASE || window.location.origin
  if (path.startsWith('/')) {
    return `${base}${path}`
  }
  return `${base}/${path}`
}

const initConsole = async () => {
  if (!props.vm) return

  // 清理之前的连接
  if (rfb.value) {
    try {
      rfb.value.disconnect()
      rfb.value = null
    } catch (e) {
      console.warn('清理旧连接时出错:', e)
    }
  }

  consoleLoading.value = true
  consoleError.value = ''

  try {
    // 创建控制台会话
    const session = await createVMConsoleSession(props.vmId, { type: 'novnc' })
    if (!session?.session_token) {
      throw new Error('未获取到控制台会话信息')
    }

    // 优先使用 proxy_url（完整的 WebSocket URL），如果没有则使用 proxy_path 构建
    let wsUrl = ''
    if (session.proxy_url) {
      wsUrl = session.proxy_url
    } else if (session.proxy_path) {
      const baseUrl = buildBackendUrl('')
      const wsProtocol = baseUrl.startsWith('https') ? 'wss' : 'ws'
      const wsHost = baseUrl.replace(/^https?:\/\//, '').replace(/\/$/, '')
      wsUrl = `${wsProtocol}://${wsHost}${session.proxy_path.startsWith('/') ? session.proxy_path : '/' + session.proxy_path}`
    } else {
      throw new Error('未获取到 WebSocket 代理路径')
    }

    const password = session.password || ''

    // 等待 DOM 更新
    await nextTick()

    const container = novncContainer.value || document.getElementById(`noVNC_container_${props.vmId}`)
    if (!container) {
      throw new Error('找不到 noVNC 容器元素，请刷新页面重试')
    }

    // 创建 noVNC 连接
    rfb.value = new RFB(container, wsUrl, {
      credentials: {
        password: password
      },
      shared: true,
      repeaterID: ''
    })

    // 配置 RFB
    rfb.value.scaleViewport = true
    rfb.value.resizeSession = false
    rfb.value.background = '#000000'
    rfb.value.qualityLevel = 6
    rfb.value.compressionLevel = 2

    // 事件监听
    rfb.value.addEventListener('connect', () => {
      consoleLoading.value = false
      consoleError.value = ''
      console.log('noVNC 连接成功')
      setTimeout(() => {
        if (rfb.value && container) {
          const resizeEvent = new Event('resize', { bubbles: true })
          container.dispatchEvent(resizeEvent)
        }
      }, 200)
    })

    rfb.value.addEventListener('disconnect', (e) => {
      consoleLoading.value = false
      const reason = e?.detail?.clean === false && e?.detail?.reason
        ? e.detail.reason
        : '连接已断开'
      consoleError.value = reason
      console.log('noVNC 断开连接:', reason, e?.detail)
    })

    rfb.value.addEventListener('credentialsrequired', () => {
      consoleError.value = '需要密码验证，但密码可能不正确'
      consoleLoading.value = false
      console.warn('noVNC 需要密码验证')
    })

    rfb.value.addEventListener('securityfailure', (e) => {
      const reason = e.detail?.reason || '未知错误'
      consoleError.value = '安全验证失败: ' + reason
      consoleLoading.value = false
      console.error('noVNC 安全验证失败:', e.detail)
    })

    rfb.value.addEventListener('serverinit', () => {
      console.log('noVNC 服务器初始化完成')
    })

    rfb.value.addEventListener('capabilities', (e) => {
      console.log('noVNC 服务器能力:', e.detail)
    })

  } catch (error) {
    consoleError.value = error.message || '初始化控制台失败'
    consoleLoading.value = false
    console.error('初始化控制台失败:', error)
  }
}

const cleanupConsole = () => {
  if (rfb.value) {
    try {
      rfb.value.disconnect()
      rfb.value = null
    } catch (e) {
      console.warn('清理控制台连接时出错:', e)
    }
  }
}

// 监听 active 变化，当切换到控制台 tab 时初始化
watch(() => props.active, (active) => {
  if (active) {
    nextTick(() => {
      setTimeout(() => {
        initConsole()
      }, 50)
    })
  } else {
    cleanupConsole()
  }
}, { immediate: true })

onBeforeUnmount(() => {
  cleanupConsole()
})
</script>

<style scoped>
.vm-console-tab {
  width: 100%;
}

.pve-console-wrapper {
  width: 100%;
  min-height: 480px;
  border: 1px solid var(--color-border-2);
  border-radius: 8px;
  background: #000;
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.novnc-container {
  width: 80%;
  max-width: 1200px;
  height: 600px;
  background: #000;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  padding: 0;
  text-align: center;
}

/* noVNC 创建的 _screen div - 确保居中显示 */
.novnc-container > div {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 80% !important;
  height: 100% !important;
  margin: 0 auto !important;
  padding: 0 !important;
  position: relative !important;
  overflow: auto !important;
}

/* noVNC 创建的 canvas - 当 scaleViewport=true 时，canvas 会按比例缩放，需要居中显示 */
.novnc-container canvas {
  display: block !important;
  margin: 0 auto !important;
  /* 不强制宽高，让 noVNC 的 scaleViewport 自动处理缩放，保持宽高比 */
  max-width: 80% !important;
  max-height: 100% !important;
  /* 确保 canvas 在容器中水平和垂直居中 */
  position: relative !important;
}

.novnc-placeholder {
  width: 80%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-3);
  text-align: center;
  flex-direction: column;
}
</style>

