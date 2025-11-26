<template>
  <div class="pve-node-monitor">
    <a-card class="filter-card" :bordered="false">
      <div class="filter-grid">
        <div class="filter-item">
          <div class="label">PVE服务器</div>
          <a-select
            v-model="selectedServer"
            placeholder="请选择服务器"
            allow-clear
            :loading="serverLoading"
          >
            <a-option v-for="item in serverOptions" :key="item.value" :value="item.value">
              {{ item.label }}
            </a-option>
          </a-select>
        </div>
        <div class="filter-item">
          <div class="label">所属节点</div>
          <a-select
            v-model="selectedNode"
            placeholder="请选择节点"
            allow-clear
            :disabled="!selectedServer"
            :loading="nodeLoading"
          >
            <a-option v-for="item in nodeOptions" :key="item.value" :value="item.value">
              {{ item.label }}
            </a-option>
          </a-select>
        </div>
        <div class="filter-item">
          <div class="label">时间范围</div>
          <a-radio-group
            v-model="timeframe"
            type="button"
            size="small"
            :options="timeframeOptions"
            @change="handleTimeframeChange"
          />
        </div>
        <div class="filter-item actions">
          <a-space>
            <div class="meta" v-if="summary.node">
              <span>状态：</span>
              <a-tag :color="getStatusTag(summary.status).color" size="small">
                {{ getStatusTag(summary.status).text }}
              </a-tag>
            </div>
            <div class="meta" v-if="summary.last_update">
              <span>最近更新：</span>
              <span>{{ formatTime(summary.last_update) }}</span>
            </div>
            <a-button type="primary" size="small" @click="loadMonitor" :loading="monitorLoading">
              <template #icon>
                <icon-refresh />
              </template>
              刷新
            </a-button>
          </a-space>
        </div>
      </div>
    </a-card>

    <a-row :gutter="16" class="summary-row">
      <a-col :span="6">
        <a-card class="stat-card" :bordered="false">
          <div class="stat-header">
            <span>CPU使用率</span>
            <a-tag size="small">{{ summary.cpu.cores || '-' }} 核</a-tag>
          </div>
          <div class="stat-value">{{ summary.cpu.percent.toFixed(1) }}%</div>
          <a-progress
            :percent="summary.cpu.percent"
            :status="getProgressStatus(summary.cpu.percent, [75, 90])"
            stroke-width="6"
          />
          <div class="stat-desc">负载：{{ formatLoad(summary.cpu.loadavg) }}</div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card" :bordered="false">
          <div class="stat-header">
            <span>内存使用率</span>
            <a-tag size="small">{{ formatBytes(summary.memory.used) }}/{{ formatBytes(summary.memory.total) }}</a-tag>
          </div>
          <div class="stat-value">{{ summary.memory.percent.toFixed(1) }}%</div>
          <a-progress
            :percent="summary.memory.percent"
            :status="getProgressStatus(summary.memory.percent, [80, 90])"
            stroke-width="6"
          />
          <div class="stat-desc">NUMA：{{ summary.memory.total ? '已启用/默认' : '-' }}</div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card" :bordered="false">
          <div class="stat-header">
            <span>存储使用率</span>
            <a-tag size="small">{{ formatBytes(summary.storage.used) }}/{{ formatBytes(summary.storage.total) }}</a-tag>
          </div>
          <div class="stat-value">{{ summary.storage.percent.toFixed(1) }}%</div>
          <a-progress
            :percent="summary.storage.percent"
            :status="getProgressStatus(summary.storage.percent, [80, 90])"
            stroke-width="6"
          />
          <div class="stat-desc">根存储使用</div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card" :bordered="false">
          <div class="stat-header">
            <span>网络吞吐</span>
            <a-tag size="small">实时</a-tag>
          </div>
          <div class="stat-value">{{ formatThroughput(summary.network.in) }}/s</div>
          <div class="stat-sub-value">出：{{ formatThroughput(summary.network.out) }}/s</div>
          <div class="stat-desc">运行时长：{{ formatDuration(summary.uptime) }}</div>
        </a-card>
      </a-col>
    </a-row>

    <a-card title="资源走势" class="chart-card" :bordered="false">
      <a-spin :loading="monitorLoading">
        <template #tip>正在加载节点监控数据...</template>
        <div v-if="metrics.length" class="chart-grid">
          <div class="chart-item">
            <div class="chart-title">CPU使用率</div>
            <div class="chart-box" ref="cpuChartRef"></div>
          </div>
          <div class="chart-item">
            <div class="chart-title">内存使用率</div>
            <div class="chart-box" ref="memoryChartRef"></div>
          </div>
          <div class="chart-item">
            <div class="chart-title">存储使用率</div>
            <div class="chart-box" ref="storageChartRef"></div>
          </div>
          <div class="chart-item">
            <div class="chart-title">网络吞吐</div>
            <div class="chart-box" ref="networkChartRef"></div>
          </div>
        </div>
        <a-empty v-else description="暂无监控数据" />
      </a-spin>
    </a-card>

    <a-card title="健康告警" class="alert-card" :bordered="false">
      <template #extra>
        <span v-if="alerts.length">共 {{ alerts.length }} 条</span>
      </template>
      <a-list v-if="alerts.length" :data="alerts" :bordered="false" :split="false">
        <template #item="{ item }">
          <a-alert
            :type="item.level === 'danger' ? 'error' : 'warning'"
            :show-icon="true"
            :closable="false"
            class="alert-item"
          >
            {{ item.message }}
          </a-alert>
        </template>
      </a-list>
      <a-empty v-else description="一切正常，暂无告警" />
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconRefresh } from '@arco-design/web-vue/es/icon'
import * as echarts from 'echarts'
import {
  getPVEServers,
  getPVEServerNodes,
  getNodeMonitor
} from '@/api/pve'

const servers = ref([])
const nodes = ref([])
const selectedServer = ref(null)
const selectedNode = ref(null)
const timeframe = ref('hour')
const metrics = ref([])
const alerts = ref([])
const serverLoading = ref(false)
const nodeLoading = ref(false)
const monitorLoading = ref(false)
let monitorRequestId = 0

const summary = reactive({
  cpu: { percent: 0, cores: 0, loadavg: null },
  memory: { total: 0, used: 0, percent: 0 },
  storage: { total: 0, used: 0, percent: 0 },
  network: { in: 0, out: 0 },
  uptime: 0,
  node: '',
  status: '',
  last_update: null
})

const timeframeOptions = [
  { label: '1小时', value: 'hour' },
  { label: '1天', value: 'day' },
  { label: '1周', value: 'week' },
  { label: '1月', value: 'month' },
  { label: '1年', value: 'year' }
]

const serverOptions = computed(() =>
  servers.value.map(item => ({
    label: `${item.name || item.host} (${item.host})`,
    value: item.id
  }))
)

const nodeOptions = computed(() =>
  nodes.value.map(item => ({
    label: item.node || item.name,
    value: item.node || item.name
  }))
)

const cpuChartRef = ref(null)
const memoryChartRef = ref(null)
const storageChartRef = ref(null)
const networkChartRef = ref(null)
let cpuChartInstance = null
let memoryChartInstance = null
let storageChartInstance = null
let networkChartInstance = null

const formattedMetrics = computed(() => {
  if (!metrics.value?.length) return []
  return metrics.value.map(item => {
    const time = item.time
    const cpuPercent = typeof item.cpu === 'number' ? +(item.cpu * 100).toFixed(2) : 0
    const memoryPercent = item.maxmem ? +(item.mem / item.maxmem * 100).toFixed(2) : 0
    const storagePercent = item.maxdisk ? +(item.disk / item.maxdisk * 100).toFixed(2) : 0
    return {
      time,
      cpu: cpuPercent,
      memory: memoryPercent,
      storage: storagePercent,
      netIn: item.netin || 0,
      netOut: item.netout || 0
    }
  })
})

function handleServerChange() {
  if (selectedServer.value) {
    loadNodes()
  } else {
    selectedNode.value = null
    metrics.value = []
    alerts.value = []
    resetSummary()
  }
}

function handleNodeChange() {
  if (selectedNode.value) {
    loadMonitor()
  } else {
    metrics.value = []
    alerts.value = []
    resetSummary()
  }
}

function handleTimeframeChange() {
  if (selectedServer.value && selectedNode.value) {
    loadMonitor()
  }
}

function resetSummary(data = {}) {
  summary.cpu.percent = data.cpu?.percent ?? 0
  summary.cpu.cores = data.cpu?.cores ?? 0
  summary.cpu.loadavg = data.cpu?.loadavg ?? null
  summary.memory.total = data.memory?.total ?? 0
  summary.memory.used = data.memory?.used ?? 0
  summary.memory.percent = data.memory?.percent ?? 0
  summary.storage.total = data.storage?.total ?? 0
  summary.storage.used = data.storage?.used ?? 0
  summary.storage.percent = data.storage?.percent ?? 0
  summary.network.in = data.network?.in ?? 0
  summary.network.out = data.network?.out ?? 0
  summary.uptime = data.uptime ?? 0
  summary.node = data.node ?? ''
  summary.status = data.status ?? ''
  summary.last_update = data.last_update ?? null
}

async function loadServers() {
  serverLoading.value = true
  try {
    const res = await getPVEServers({ page_size: 200 })
    const data = Array.isArray(res) ? res : res?.results || []
    servers.value = data.filter(item => item.is_active !== false)
    if (!selectedServer.value && servers.value.length) {
      selectedServer.value = servers.value[0].id
    }
  } catch (error) {
    Message.error('获取服务器列表失败：' + (error.message || '未知错误'))
  } finally {
    serverLoading.value = false
  }
}

async function loadNodes() {
  if (!selectedServer.value) return
  nodeLoading.value = true
  try {
    const res = await getPVEServerNodes(selectedServer.value)
    nodes.value = Array.isArray(res) ? res : res?.data || []
    if (nodes.value.length && !selectedNode.value) {
      selectedNode.value = nodes.value[0].node || nodes.value[0].name
    } else if (selectedNode.value) {
      const exists = nodes.value.some(item => (item.node || item.name) === selectedNode.value)
      if (!exists) {
        selectedNode.value = nodes.value[0]?.node || nodes.value[0]?.name || null
      }
    }
    if (!nodes.value.length) {
      selectedNode.value = null
    }
  } catch (error) {
    Message.error('获取节点列表失败：' + (error.message || '未知错误'))
    nodes.value = []
    selectedNode.value = null
  } finally {
    nodeLoading.value = false
  }
}

async function loadMonitor() {
  if (!selectedServer.value || !selectedNode.value) {
    return
  }
  const requestId = ++monitorRequestId
  monitorLoading.value = true
  try {
    const res = await getNodeMonitor(selectedServer.value, selectedNode.value, { timeframe: timeframe.value })
    if (requestId !== monitorRequestId) {
      return
    }
    const result = res?.data || res || {}
    resetSummary(result.summary || {})
    metrics.value = Array.isArray(result.metrics) ? result.metrics : []
    alerts.value = Array.isArray(result.alerts) ? result.alerts : []
    await nextTick()
    updateCharts()
  } catch (error) {
    if (requestId !== monitorRequestId) {
      return
    }
    Message.error('获取节点监控数据失败：' + (error.message || '未知错误'))
    metrics.value = []
    alerts.value = []
    resetSummary()
  } finally {
    if (requestId === monitorRequestId) {
      monitorLoading.value = false
    }
  }
}

function updateCharts() {
  const data = formattedMetrics.value
  cpuChartInstance = renderLineChart(cpuChartRef, cpuChartInstance, data, {
    seriesKey: 'cpu',
    name: 'CPU %',
    color: '#165DFF',
    yAxisFormatter: value => `${value}%`
  })
  memoryChartInstance = renderLineChart(memoryChartRef, memoryChartInstance, data, {
    seriesKey: 'memory',
    name: '内存 %',
    color: '#00B42A',
    yAxisFormatter: value => `${value}%`
  })
  storageChartInstance = renderLineChart(storageChartRef, storageChartInstance, data, {
    seriesKey: 'storage',
    name: '存储 %',
    color: '#F77234',
    yAxisFormatter: value => `${value}%`
  })
  networkChartInstance = renderLineChart(networkChartRef, networkChartInstance, data, {
    seriesKey: ['netIn', 'netOut'],
    name: ['入站', '出站'],
    color: ['#14C9C9', '#F53F3F'],
    yAxisFormatter: value => formatThroughput(value, true)
  })
}

function renderLineChart(refEl, chartInstance, data, config) {
  if (!refEl.value) {
    if (chartInstance) {
      chartInstance.dispose()
    }
    return null
  }
  if (!chartInstance) {
    chartInstance = echarts.init(refEl.value)
  }
  const timeData = data.map(item => item.time)
  const series = []
  if (Array.isArray(config.seriesKey)) {
    config.seriesKey.forEach((key, idx) => {
      series.push({
        name: config.name[idx] || key,
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: data.map(item => item[key]),
        areaStyle: {
          opacity: 0.08
        },
        lineStyle: {
          width: 2,
          color: config.color[idx]
        }
      })
    })
  } else {
    series.push({
      name: config.name,
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: data.map(item => item[config.seriesKey]),
      areaStyle: {
        opacity: 0.08
      },
      lineStyle: {
        width: 2,
        color: config.color
      }
    })
  }
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: params => {
        if (!params?.length) return ''
        const time = formatTime(params[0].axisValue)
        const lines = params.map(item => {
          const color = item.color
          const label = item.seriesName
          const value = config.yAxisFormatter ? config.yAxisFormatter(item.value) : item.value
          return `<span style="display:inline-block;margin-right:4px;width:8px;height:8px;border-radius:50%;background:${color}"></span>${label}: ${value}`
        })
        return `${time}<br/>${lines.join('<br/>')}`
      }
    },
    grid: {
      left: 30,
      right: 20,
      top: 30,
      bottom: 20
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: timeData,
      axisLabel: {
        formatter: value => formatTime(value, true)
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: value => config.yAxisFormatter ? config.yAxisFormatter(value) : value
      }
    },
    series
  }
  chartInstance.setOption(option)
  return chartInstance
}

function formatBytes(value) {
  if (!value && value !== 0) return '-'
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  let index = 0
  let num = Number(value)
  while (num >= 1024 && index < units.length - 1) {
    num /= 1024
    index++
  }
  return `${num.toFixed(num >= 10 || num < 1 ? 1 : 2)} ${units[index]}`
}

function formatThroughput(value, short = false) {
  if (!value && value !== 0) return '-'
  const units = [
    { unit: 'B', scale: 1 },
    { unit: 'KB', scale: 1024 },
    { unit: 'MB', scale: 1024 ** 2 },
    { unit: 'GB', scale: 1024 ** 3 }
  ]
  let num = Number(value)
  let idx = 0
  while (num >= 1024 && idx < units.length - 1) {
    num /= 1024
    idx++
  }
  const fixed = num >= 10 || short ? 1 : 2
  return `${num.toFixed(fixed)} ${units[idx].unit}${short ? '' : '/s'}`
}

function formatDuration(seconds) {
  const sec = Number(seconds || 0)
  if (!sec) return '-'
  const days = Math.floor(sec / 86400)
  const hours = Math.floor((sec % 86400) / 3600)
  const minutes = Math.floor((sec % 3600) / 60)
  if (days > 0) return `${days}天${hours}小时`
  if (hours > 0) return `${hours}小时${minutes}分钟`
  if (minutes > 0) return `${minutes}分钟`
  return `${sec}s`
}

function formatTime(timestamp, short = false) {
  if (!timestamp) return '-'
  const date = new Date(Number(timestamp))
  if (Number.isNaN(date.getTime())) return '-'
  if (short) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).replace(/\//g, '-')
}

function formatLoad(loadavg) {
  if (!loadavg && loadavg !== 0) return '-'
  if (Array.isArray(loadavg)) {
    return loadavg.map(item => Number(item || 0).toFixed(2)).join(' / ')
  }
  return Number(loadavg).toFixed(2)
}

function getProgressStatus(percent, thresholds = []) {
  if (percent >= (thresholds[1] || 90)) return 'danger'
  if (percent >= (thresholds[0] || 75)) return 'warning'
  return 'success'
}

function getStatusTag(status) {
  if (!status) {
    return { color: 'gray', text: '未知' }
  }
  const lower = status.toLowerCase()
  if (lower === 'online' || lower === 'running') {
    return { color: 'green', text: '在线' }
  }
  if (lower === 'offline') {
    return { color: 'red', text: '离线' }
  }
  return { color: 'orange', text: status }
}

function handleResize() {
  cpuChartInstance?.resize()
  memoryChartInstance?.resize()
  storageChartInstance?.resize()
  networkChartInstance?.resize()
}

watch(selectedServer, () => {
  handleServerChange()
})

watch(selectedNode, () => {
  handleNodeChange()
})

watch(formattedMetrics, () => {
  nextTick(() => updateCharts())
})

onMounted(() => {
  loadServers()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  cpuChartInstance?.dispose()
  memoryChartInstance?.dispose()
  storageChartInstance?.dispose()
  networkChartInstance?.dispose()
})
</script>

<style scoped>
.pve-node-monitor {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-card {
  padding-bottom: 8px;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  align-items: center;
}

.filter-item .label {
  font-size: 13px;
  color: var(--color-text-2);
  margin-bottom: 6px;
}

.filter-item.actions {
  justify-self: flex-end;
  text-align: right;
}

.filter-item .meta {
  font-size: 12px;
  color: var(--color-text-2);
}

.summary-row {
  margin-bottom: 16px;
}

.stat-card {
  min-height: 180px;
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: var(--color-text-1);
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  margin: 12px 0 8px;
}

.stat-sub-value {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
}

.stat-desc {
  font-size: 12px;
  color: var(--color-text-2);
  margin-top: 6px;
}

.chart-card {
  min-height: 460px;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.chart-item {
  background: var(--color-bg-2);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
}

.chart-title {
  font-size: 14px;
  margin-bottom: 4px;
  color: var(--color-text-1);
}

.chart-box {
  flex: 1;
  min-height: 180px;
}

.alert-card .alert-item {
  margin-bottom: 12px;
}

@media (max-width: 768px) {
  .filter-grid {
    grid-template-columns: 1fr;
  }
  .stat-card {
    margin-bottom: 16px;
  }
}
</style>

