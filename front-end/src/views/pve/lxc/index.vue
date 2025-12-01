<template>
  <div class="lxc-container-page">
    <a-card>
      <template #title>
        <a-typography-title :heading="4">LXC 容器管理</a-typography-title>
      </template>

      <div class="toolbar">
        <a-space wrap>
          <a-select
            v-model="selectedServer"
            placeholder="选择PVE服务器"
            style="width: 220px"
            allow-clear
            @change="handleServerChange"
          >
            <a-option v-for="server in servers" :key="server.id" :value="server.id">
              {{ server.name }}
            </a-option>
          </a-select>
          <a-input-search
            v-model="searchText"
            placeholder="搜索容器名称、ID或IP"
            style="width: 280px"
            allow-clear
            @search="handleSearch"
            @clear="handleSearch"
          />
          <a-button type="outline" :loading="syncing" @click="handleSyncAll">
            <template #icon>
              <icon-refresh />
            </template>
            同步容器
          </a-button>
          <a-button type="secondary" @click="fetchData">刷新</a-button>
        </a-space>
      </div>

      <a-table
        row-key="id"
        :columns="columns"
        :data="tableData"
        :loading="loading"
        :pagination="pagination"
        :hoverable="true"
        @page-change="handlePageChange"
        @page-size-change="handlePageSizeChange"
      >
        <template #status="{ record }">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>
        <template #actions="{ record }">
          <a-space size="mini">
            <a-link @click="openDetail(record)">详情</a-link>
            <a-dropdown>
              <a-button size="small" type="text">操作</a-button>
              <template #content>
                <a-doption v-if="record.status !== 'running'" @click="handleAction(record, 'start')">
                  启动
                </a-doption>
                <a-doption v-if="record.status === 'running'" @click="handleAction(record, 'stop')">
                  停止
                </a-doption>
                <a-doption v-if="record.status === 'running'" @click="handleAction(record, 'shutdown')">
                  关闭
                </a-doption>
                <a-doption @click="handleAction(record, 'reboot')">重启</a-doption>
                <a-doption @click="handleSyncStatus(record)">同步状态</a-doption>
                <a-doption status="danger" @click="handleDelete(record)">删除记录</a-doption>
              </template>
            </a-dropdown>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <a-drawer
      v-model:visible="detailVisible"
      :width="520"
      title="容器详情"
      unmount-on-close
    >
      <template v-if="detailRecord">
        <a-descriptions :column="1" size="large">
          <a-descriptions-item label="容器ID">{{ detailRecord.vmid }}</a-descriptions-item>
          <a-descriptions-item label="名称">{{ detailRecord.name }}</a-descriptions-item>
          <a-descriptions-item label="服务器">{{ detailRecord.server_name }}</a-descriptions-item>
          <a-descriptions-item label="节点">{{ detailRecord.node }}</a-descriptions-item>
          <a-descriptions-item label="状态">{{ getStatusText(detailRecord.status) }}</a-descriptions-item>
          <a-descriptions-item label="CPU核心数">{{ detailRecord.cpu_cores }}</a-descriptions-item>
          <a-descriptions-item label="内存(MB)">{{ detailRecord.memory_mb }}</a-descriptions-item>
          <a-descriptions-item label="磁盘(GB)">{{ detailRecord.disk_gb }}</a-descriptions-item>
          <a-descriptions-item label="IP地址">{{ detailRecord.ip_address || '-' }}</a-descriptions-item>
          <a-descriptions-item label="描述">{{ detailRecord.description || '无' }}</a-descriptions-item>
          <a-descriptions-item label="最近同步时间">{{ detailRecord.updated_at }}</a-descriptions-item>
        </a-descriptions>
        <a-divider>原始配置</a-divider>
        <a-alert type="info" show-icon>
          下方展示存储在数据库中的 PVE 配置快照，便于排查问题。
        </a-alert>
        <pre class="config-preview">{{ formatConfig(detailRecord.pve_config) }}</pre>
      </template>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { IconRefresh } from '@arco-design/web-vue/es/icon'
import {
  getPVEServers,
  getLXCContainers,
  lxcAction,
  syncLXCStatus,
  syncAllLXCContainers,
  deleteLXCContainer
} from '@/api/pve'

const columns = [
  { title: 'ID', dataIndex: 'id', width: 80 },
  { title: '服务器', dataIndex: 'server_name', width: 160 },
  { title: '容器ID', dataIndex: 'vmid', width: 100 },
  { title: '名称', dataIndex: 'name', width: 200 },
  { title: '节点', dataIndex: 'node', width: 120 },
  { title: '状态', slotName: 'status', width: 100 },
  { title: 'CPU', dataIndex: 'cpu_cores', width: 80 },
  { title: '内存(MB)', dataIndex: 'memory_mb', width: 110 },
  { title: '磁盘(GB)', dataIndex: 'disk_gb', width: 110 },
  { title: 'IP地址', dataIndex: 'ip_address', width: 160 },
  { title: '更新时间', dataIndex: 'updated_at', width: 180 },
  { title: '操作', slotName: 'actions', width: 140, fixed: 'right' }
]

const loading = ref(false)
const syncing = ref(false)
const servers = ref([])
const selectedServer = ref(null)
const searchText = ref('')
const tableData = ref([])
const detailVisible = ref(false)
const detailRecord = ref(null)

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showTotal: true,
  showPageSize: true
})

const getStatusColor = (status) => {
  const colorMap = {
    running: 'green',
    stopped: 'red',
    paused: 'orange',
    unknown: 'gray'
  }
  return colorMap[status] || 'gray'
}

const getStatusText = (status) => {
  const textMap = {
    running: '运行中',
    stopped: '已停止',
    paused: '已暂停',
    unknown: '未知'
  }
  return textMap[status] || '未知'
}

const formatConfig = (config) => {
  try {
    return JSON.stringify(config || {}, null, 2)
  } catch (error) {
    return '{}'
  }
}

const fetchServers = async () => {
  try {
    const res = await getPVEServers({ is_active: true })
    if (Array.isArray(res)) {
      servers.value = res
    } else if (res.results) {
      servers.value = res.results
    }
  } catch (error) {
    Message.error('获取服务器列表失败：' + (error.message || '未知错误'))
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize
    }
    if (selectedServer.value) {
      params.server = selectedServer.value
    }
    if (searchText.value) {
      params.search = searchText.value
    }
    const res = await getLXCContainers(params)
    if (Array.isArray(res)) {
      tableData.value = res
      pagination.total = res.length
    } else if (res.results) {
      tableData.value = res.results
      pagination.total = res.count || 0
    } else {
      tableData.value = []
      pagination.total = 0
    }
  } catch (error) {
    Message.error('获取容器列表失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  fetchData()
}

const handleServerChange = () => {
  pagination.current = 1
  fetchData()
}

const handlePageChange = (page) => {
  pagination.current = page
  fetchData()
}

const handlePageSizeChange = (size) => {
  pagination.pageSize = size
  pagination.current = 1
  fetchData()
}

const handleAction = async (record, action) => {
  try {
    await lxcAction(record.id, action)
    Message.success(`操作 ${action} 已提交`)
    fetchData()
  } catch (error) {
    Message.error('执行操作失败：' + (error.message || '未知错误'))
  }
}

const handleSyncStatus = async (record) => {
  try {
    await syncLXCStatus(record.id)
    Message.success('状态已同步')
    fetchData()
  } catch (error) {
    Message.error('同步状态失败：' + (error.message || '未知错误'))
  }
}

const handleDelete = (record) => {
  Modal.confirm({
    title: '确认删除',
    content: `仅删除平台记录，不会删除 PVE 上的 CT ${record.vmid}，确认继续？`,
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try {
        await deleteLXCContainer(record.id)
        Message.success('记录已删除')
        fetchData()
      } catch (error) {
        Message.error('删除失败：' + (error.message || '未知错误'))
      }
    }
  })
}

const handleSyncAll = async () => {
  syncing.value = true
  try {
    const payload = {}
    if (selectedServer.value) {
      payload.server_id = selectedServer.value
    }
    const res = await syncAllLXCContainers(payload)
    Message.success(`同步完成，共处理 ${res.synced || 0} 条`)
    fetchData()
  } catch (error) {
    Message.error('同步失败：' + (error.message || '未知错误'))
  } finally {
    syncing.value = false
  }
}

const openDetail = (record) => {
  detailRecord.value = { ...record }
  detailVisible.value = true
}

onMounted(() => {
  fetchServers()
  fetchData()
})
</script>

<style scoped>
.lxc-container-page {
  padding: 16px;
}

.toolbar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.config-preview {
  margin-top: 12px;
  padding: 12px;
  background-color: var(--color-fill-2);
  border-radius: 6px;
  max-height: 320px;
  overflow: auto;
  font-family: SFMono-Regular, Consolas, Menlo, monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>

