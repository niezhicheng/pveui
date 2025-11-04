<template>
  <div class="monitor-page">
    <a-card>
      <template #title>
        <a-space>
          <a-typography-title :heading="4">系统监控</a-typography-title>
          <a-tag>{{ meta.platform.system }} {{ meta.platform.release }}</a-tag>
          <a-tag>Python {{ meta.platform.python }}</a-tag>
          <a-tag>Uptime: {{ formatSeconds(meta.uptime_seconds) }}</a-tag>
        </a-space>
      </template>

      <div class="toolbar">
        <a-space>
          <a-button type="primary" @click="fetchData" :loading="loading">刷新</a-button>
          <a-switch v-model="autoRefresh" checked-text="自动刷新" unchecked-text="手动" />
          <a-input-number v-model="intervalSec" :min="2" :max="120" />
          <a-typography-text type="secondary">秒</a-typography-text>
        </a-space>
      </div>

      <a-grid :cols="4" :col-gap="16" :row-gap="16">
        <a-grid-item>
          <a-card title="CPU">
            <a-statistic title="使用率" :value="meta.cpu.percent" suffix="%" />
            <a-divider />
            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="逻辑核">{{ meta.cpu.count_logical }}</a-descriptions-item>
              <a-descriptions-item label="物理核">{{ meta.cpu.count_physical }}</a-descriptions-item>
              <a-descriptions-item label="Load Avg">{{ meta.cpu.load_avg?.join(' / ') || '-' }}</a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-grid-item>

        <a-grid-item>
          <a-card title="内存">
            <a-statistic title="使用率" :value="meta.memory.percent" suffix="%" />
            <a-divider />
            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="总量">{{ formatBytes(meta.memory.total) }}</a-descriptions-item>
              <a-descriptions-item label="已用">{{ formatBytes(meta.memory.used) }}</a-descriptions-item>
              <a-descriptions-item label="可用">{{ formatBytes(meta.memory.available) }}</a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-grid-item>

        <a-grid-item>
          <a-card title="Swap">
            <a-statistic title="使用率" :value="meta.swap.percent" suffix="%" />
            <a-divider />
            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="总量">{{ formatBytes(meta.swap.total) }}</a-descriptions-item>
              <a-descriptions-item label="已用">{{ formatBytes(meta.swap.used) }}</a-descriptions-item>
              <a-descriptions-item label="空闲">{{ formatBytes(meta.swap.free) }}</a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-grid-item>

        <a-grid-item>
          <a-card title="网络">
            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="发送">{{ formatBytes(meta.network.bytes_sent) }}</a-descriptions-item>
              <a-descriptions-item label="接收">{{ formatBytes(meta.network.bytes_recv) }}</a-descriptions-item>
              <a-descriptions-item label="发送包">{{ meta.network.packets_sent }}</a-descriptions-item>
              <a-descriptions-item label="接收包">{{ meta.network.packets_recv }}</a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-grid-item>
      </a-grid>

      <a-card style="margin-top: 16px" title="磁盘">
        <a-table :data="meta.disks" :loading="loading" :pagination="false">
          <template #columns>
            <a-table-column title="设备" data-index="device" :width="200" />
            <a-table-column title="挂载点" data-index="mountpoint" :width="200" />
            <a-table-column title="类型" data-index="fstype" :width="120" />
            <a-table-column title="总量" :width="160">
              <template #cell="{ record }">{{ formatBytes(record.total) }}</template>
            </a-table-column>
            <a-table-column title="已用" :width="160">
              <template #cell="{ record }">{{ formatBytes(record.used) }}</template>
            </a-table-column>
            <a-table-column title="可用" :width="160">
              <template #cell="{ record }">{{ formatBytes(record.free) }}</template>
            </a-table-column>
            <a-table-column title="使用率">
              <template #cell="{ record }">
                <a-progress :percent="record.percent" :show-text="true" />
              </template>
            </a-table-column>
          </template>
        </a-table>
      </a-card>
    </a-card>
  </div>
  </template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getSystemMetrics } from '@/api/system'

const loading = ref(false)
const autoRefresh = ref(true)
const intervalSec = ref(5)
let timer = null

const meta = reactive({
  platform: { system: '-', release: '-', python: '-' },
  uptime_seconds: 0,
  cpu: { percent: 0, count_logical: 0, count_physical: 0, load_avg: [] },
  memory: { total: 0, available: 0, used: 0, free: 0, percent: 0 },
  swap: { total: 0, used: 0, free: 0, percent: 0 },
  disks: [],
  network: { bytes_sent: 0, bytes_recv: 0, packets_sent: 0, packets_recv: 0 },
})

async function fetchData() {
  loading.value = true
  try {
    const res = await getSystemMetrics()
    Object.assign(meta, res)
  } catch (e) {
    Message.error('获取系统指标失败')
  } finally {
    loading.value = false
  }
}

function startTimer() {
  stopTimer()
  if (autoRefresh.value) {
    timer = setInterval(fetchData, Math.max(2, intervalSec.value) * 1000)
  }
}

function stopTimer() {
  if (timer) { clearInterval(timer); timer = null }
}

watch([autoRefresh, intervalSec], startTimer)

onMounted(() => {
  fetchData()
  startTimer()
})

onBeforeUnmount(() => {
  stopTimer()
})

function formatBytes(n) {
  if (!n && n !== 0) return '-'
  const units = ['B','KB','MB','GB','TB']
  let v = Number(n)
  let i = 0
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++ }
  return `${v.toFixed(2)} ${units[i]}`
}

function formatSeconds(sec) {
  const s = Number(sec || 0)
  const d = Math.floor(s / 86400)
  const h = Math.floor((s % 86400) / 3600)
  const m = Math.floor((s % 3600) / 60)
  const r = s % 60
  const parts = []
  if (d) parts.push(`${d}d`)
  if (h) parts.push(`${h}h`)
  if (m) parts.push(`${m}m`)
  parts.push(`${r}s`)
  return parts.join(' ')
}
</script>

<style scoped>
.monitor-page { padding: 20px; }
.toolbar { margin-bottom: 16px; }
</style>


