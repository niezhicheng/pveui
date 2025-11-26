<template>
  <div class="vm-tasks-tab">
    <a-card :bordered="false">
      <template #title>
        <div class="tasks-header">
          <span>任务历史</span>
          <div class="tasks-actions">
            <a-button size="small" @click="loadData" :loading="loading">刷新</a-button>
          </div>
        </div>
      </template>

      <a-table
        :data="tasks"
        :loading="loading"
        :pagination="false"
        :scroll="{ y: 400 }"
        size="small"
        row-key="upid"
      >
        <template #columns>
          <a-table-column title="任务类型" data-index="type" :width="150">
            <template #cell="{ record }">
              <a-tag :color="getTaskTypeColor(record.type)">
                {{ getTaskTypeName(record.type) }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="状态" data-index="status" :width="120">
            <template #cell="{ record }">
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusName(record.status) }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="开始时间" :width="180">
            <template #cell="{ record }">
              {{ formatTime(record.starttime) }}
            </template>
          </a-table-column>
          <a-table-column title="结束时间" :width="180">
            <template #cell="{ record }">
              {{ formatTime(record.endtime) }}
            </template>
          </a-table-column>
          <a-table-column title="用户" data-index="user" :width="150" />
          <a-table-column title="操作" :width="100">
            <template #cell="{ record }">
              <a-button type="text" size="small" @click="handleViewLog(record)">
                查看日志
              </a-button>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </a-card>

    <!-- 任务日志对话框 -->
    <a-modal
      v-model:visible="logVisible"
      :title="`任务日志 - ${currentTask?.type || ''}`"
      :width="800"
      :footer="false"
      unmount-on-close
    >
      <div class="log-container">
        <a-spin :loading="logLoading" style="width: 100%;">
          <pre class="log-content">{{ logContent }}</pre>
        </a-spin>
      </div>
      <div class="modal-footer">
        <a-button @click="logVisible = false">关闭</a-button>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import dayjs from 'dayjs'
import { Message } from '@arco-design/web-vue'
import { getVMTasks, getVMTaskLog } from '@/api/pve'

const props = defineProps({
  vm: {
    type: Object,
    default: null
  },
  vmId: {
    type: [Number, String],
    default: null
  }
})

const loading = ref(false)
const tasks = ref([])
const logVisible = ref(false)
const logLoading = ref(false)
const logContent = ref('')
const currentTask = ref(null)
const refreshTimer = ref(null)
const REFRESH_INTERVAL = 5000

const taskTypeMap = {
  qmstart: '启动',
  qmstop: '停止',
  qmshutdown: '关机',
  qmreboot: '重启',
  qmsnapshot: '快照',
  qmrollback: '回滚',
  qmrestore: '恢复',
  vzdump: '备份',
  qmconfig: '配置',
  qmclone: '克隆',
  qmmigrate: '迁移',
  qmdel: '删除'
}

const getTaskTypeName = (type) => {
  return taskTypeMap[type] || type || '未知'
}

const getTaskTypeColor = (type) => {
  const colorMap = {
    qmstart: 'green',
    qmstop: 'red',
    qmshutdown: 'orange',
    qmreboot: 'blue',
    qmsnapshot: 'purple',
    qmrollback: 'cyan',
    qmrestore: 'lime',
    vzdump: 'gold',
    qmconfig: 'gray',
    qmclone: 'magenta',
    qmmigrate: 'blue',
    qmdel: 'red'
  }
  return colorMap[type] || 'gray'
}

const getStatusName = (status) => {
  const statusMap = {
    running: '运行中',
    stopped: '已完成',
    OK: '成功',
    ok: '成功'
  }
  return statusMap[status] || status || '未知'
}

const getStatusColor = (status) => {
  if (!status) return 'gray'
  const lowerStatus = String(status).toLowerCase()
  if (lowerStatus === 'ok' || lowerStatus === 'stopped') {
    return 'green'
  }
  if (lowerStatus === 'running') {
    return 'blue'
  }
  return 'gray'
}

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  return dayjs.unix(timestamp).format('YYYY-MM-DD HH:mm:ss')
}

const loadData = async () => {
  if (!props.vmId) {
    tasks.value = []
    return
  }
  if (loading.value) {
    return
  }
  loading.value = true
  try {
    const res = await getVMTasks(props.vmId, { limit: 100, task_status: 'all' })
    tasks.value = res?.tasks || []
  } catch (error) {
    Message.error('获取任务列表失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const handleViewLog = async (task) => {
  if (!task || !task.upid) {
    Message.warning('任务信息不完整')
    return
  }
  currentTask.value = task
  logVisible.value = true
  logLoading.value = true
  logContent.value = ''
  
  try {
    const res = await getVMTaskLog(props.vmId, {
      upid: task.upid,
      start: 0,
      limit: 500
    })
    const logs = res?.log || []
    logContent.value = logs.join('\n') || '暂无日志内容'
  } catch (error) {
    logContent.value = '获取日志失败：' + (error.message || '未知错误')
  } finally {
    logLoading.value = false
  }
}

const startAutoRefresh = () => {
  stopAutoRefresh()
  refreshTimer.value = setInterval(() => {
    loadData()
  }, REFRESH_INTERVAL)
}

const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

watch(
  () => props.vmId,
  (val, oldVal) => {
    if (val && val !== oldVal) {
      loadData()
      startAutoRefresh()
    } else if (!val) {
      stopAutoRefresh()
    }
  }
)

onMounted(() => {
  if (props.vmId) {
    loadData()
    startAutoRefresh()
  }
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.vm-tasks-tab {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.vm-tasks-tab :deep(.arco-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.vm-tasks-tab :deep(.arco-card-body) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.tasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tasks-actions {
  display: flex;
  align-items: center;
}

.log-container {
  max-height: 500px;
  overflow-y: auto;
  background: #f5f5f5;
  border-radius: 4px;
  padding: 12px;
}

.log-content {
  margin: 0;
  font-family: var(--font-family-code, 'Courier New', monospace);
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  color: #333;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>

