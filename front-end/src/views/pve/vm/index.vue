<template>
  <div class="virtual-machine">
    <a-card>
      <template #title>
        <a-typography-title :heading="4">虚拟机管理</a-typography-title>
      </template>

      <!-- 工具栏 -->
      <div class="toolbar">
        <a-space>
          <a-select
            v-model="selectedServer"
            placeholder="选择PVE服务器"
            style="width: 200px"
            allow-clear
            @change="handleServerChange"
          >
            <a-option
              v-for="server in servers"
              :key="server.id"
              :value="server.id"
            >
              {{ server.name }}
            </a-option>
          </a-select>
          <a-input-search
            v-model="searchText"
            placeholder="搜索虚拟机名称或ID"
            style="width: 300px"
            @search="handleSearch"
            @clear="handleSearch"
            allow-clear
          />
          <a-button type="primary" @click="handleCreate">
            <template #icon>
              <icon-plus />
            </template>
            创建虚拟机
          </a-button>
        </a-space>
      </div>

      <!-- 表格 -->
      <a-table
        :columns="columns"
        :data="tableData"
        :loading="loading"
        :pagination="pagination"
        @page-change="handlePageChange"
        @page-size-change="handlePageSizeChange"
        :bordered="false"
        :hoverable="true"
        style="margin-top: 16px"
      >
        <template #status="{ record }">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>

        <template #actions="{ record }">
          <a-dropdown>
            <a-button type="text" size="small">
              操作
              <icon-down />
            </a-button>
            <template #content>
              <a-doption v-if="record.status !== 'running'" @click="handleVMAction(record, 'start')">
                启动
              </a-doption>
              <a-doption v-if="record.status === 'running'" @click="handleVMAction(record, 'stop')">
                停止
              </a-doption>
              <a-doption v-if="record.status === 'running'" @click="handleVMAction(record, 'shutdown')">
                关闭
              </a-doption>
              <a-doption v-if="record.status === 'running'" @click="handleVMAction(record, 'reboot')">
                重启
              </a-doption>
              <a-doption @click="handleSyncStatus(record)">同步状态</a-doption>
              <a-doption @click="handleViewDetail(record)">查看详情</a-doption>
              <a-doption status="danger" @click="handleDelete(record)">删除</a-doption>
            </template>
          </a-dropdown>
        </template>
      </a-table>
    </a-card>

    <!-- 创建虚拟机对话框 -->
    <a-modal
      v-model:visible="createFormVisible"
      title="创建虚拟机"
      @before-ok="handleCreateSubmit"
      @cancel="handleCreateCancel"
      :width="800"
    >
      <a-form
        ref="createFormRef"
        :model="createFormData"
        :rules="createFormRules"
        layout="vertical"
      >
        <a-form-item field="server_id" label="PVE服务器">
          <a-select
            v-model="createFormData.server_id"
            placeholder="请选择PVE服务器"
            @change="handleServerSelect"
          >
            <a-option
              v-for="server in servers"
              :key="server.id"
              :value="server.id"
            >
              {{ server.name }}
            </a-option>
          </a-select>
        </a-form-item>

        <a-form-item field="node" label="节点">
          <a-select
            v-model="createFormData.node"
            placeholder="请选择节点"
            :loading="nodesLoading"
            :disabled="!createFormData.server_id"
            @change="handleNodeChange"
          >
            <a-option
              v-for="node in nodes"
              :key="node.node"
              :value="node.node"
            >
              {{ node.node }} ({{ node.status || '未知' }})
            </a-option>
          </a-select>
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item field="vmid" label="虚拟机ID（可选）">
              <a-input-number
                v-model="createFormData.vmid"
                :min="100"
                placeholder="留空自动分配"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item field="name" label="虚拟机名称">
              <a-input
                v-model="createFormData.name"
                placeholder="请输入虚拟机名称"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item field="cores" label="CPU核心数">
              <a-input-number
                v-model="createFormData.cores"
                :min="1"
                :max="32"
                placeholder="默认1"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item field="memory" label="内存(MB)">
              <a-input-number
                v-model="createFormData.memory"
                :min="512"
                :step="512"
                placeholder="默认512"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item field="disk_size" label="磁盘大小">
              <a-input
                v-model="createFormData.disk_size"
                placeholder="如：10G"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item field="disk_storage" label="存储">
              <a-select
                v-model="createFormData.disk_storage"
                placeholder="请选择存储"
                :loading="storageLoading"
                :disabled="!createFormData.node"
              >
                <a-option
                  v-for="storage in storages"
                  :key="storage.storage"
                  :value="storage.storage"
                >
                  {{ storage.storage }} ({{ storage.type }})
                </a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item field="network_bridge" label="网络桥接">
              <a-input
                v-model="createFormData.network_bridge"
                placeholder="默认vmbr0"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item field="ostype" label="操作系统类型">
          <a-select v-model="createFormData.ostype" placeholder="请选择操作系统类型">
            <a-option value="l26">Linux 2.6+</a-option>
            <a-option value="l24">Linux 2.4</a-option>
            <a-option value="w2k">Windows 2000</a-option>
            <a-option value="w2k3">Windows 2003</a-option>
            <a-option value="w2k8">Windows 2008</a-option>
            <a-option value="wvista">Windows Vista</a-option>
            <a-option value="win7">Windows 7</a-option>
            <a-option value="win8">Windows 8</a-option>
            <a-option value="win10">Windows 10</a-option>
            <a-option value="win11">Windows 11</a-option>
            <a-option value="other">其他</a-option>
          </a-select>
        </a-form-item>

        <a-form-item field="iso" label="ISO镜像（可选）">
          <a-input
            v-model="createFormData.iso"
            placeholder="ISO镜像文件名，如：ubuntu-22.04.iso"
          />
        </a-form-item>

        <a-form-item field="description" label="描述">
          <a-textarea
            v-model="createFormData.description"
            placeholder="请输入虚拟机描述"
            :auto-size="{ minRows: 2, maxRows: 4 }"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 详情对话框 -->
    <a-modal
      v-model:visible="detailVisible"
      title="虚拟机详情"
      :footer="false"
      :width="800"
    >
      <a-descriptions
        v-if="currentVM"
        :column="2"
        bordered
      >
        <a-descriptions-item label="虚拟机ID">{{ currentVM.vmid }}</a-descriptions-item>
        <a-descriptions-item label="名称">{{ currentVM.name }}</a-descriptions-item>
        <a-descriptions-item label="节点">{{ currentVM.node }}</a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="getStatusColor(currentVM.status)">
            {{ getStatusText(currentVM.status) }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="CPU核心数">{{ currentVM.cpu_cores }}</a-descriptions-item>
        <a-descriptions-item label="内存">{{ currentVM.memory_mb }} MB</a-descriptions-item>
        <a-descriptions-item label="磁盘">{{ currentVM.disk_gb }} GB</a-descriptions-item>
        <a-descriptions-item label="IP地址">{{ currentVM.ip_address || '未分配' }}</a-descriptions-item>
        <a-descriptions-item label="描述" :span="2">{{ currentVM.description || '无' }}</a-descriptions-item>
        <a-descriptions-item label="创建时间" :span="2">{{ currentVM.created_at }}</a-descriptions-item>
      </a-descriptions>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { IconPlus, IconDown } from '@arco-design/web-vue/es/icon'
import {
  getPVEServers,
  getPVEServerNodes,
  getNodeStorage,
  getVirtualMachines,
  createVirtualMachine,
  deleteVirtualMachine,
  vmAction,
  syncVMStatus
} from '@/api/pve'

const columns = [
  { title: 'ID', dataIndex: 'id', width: 80 },
  { title: '服务器', dataIndex: 'server_name', width: 150 },
  { title: '虚拟机ID', dataIndex: 'vmid', width: 100 },
  { title: '名称', dataIndex: 'name', width: 200 },
  { title: '节点', dataIndex: 'node', width: 120 },
  { title: '状态', dataIndex: 'status', slotName: 'status', width: 100 },
  { title: 'CPU', dataIndex: 'cpu_cores', width: 80 },
  { title: '内存(MB)', dataIndex: 'memory_mb', width: 100 },
  { title: '磁盘(GB)', dataIndex: 'disk_gb', width: 100 },
  { title: 'IP地址', dataIndex: 'ip_address', width: 150 },
  { title: '创建时间', dataIndex: 'created_at', width: 180 },
  { title: '操作', slotName: 'actions', width: 120, fixed: 'right' }
]

const loading = ref(false)
const searchText = ref('')
const selectedServer = ref(null)
const tableData = ref([])
const servers = ref([])
const createFormVisible = ref(false)
const detailVisible = ref(false)
const currentVM = ref(null)
const nodesLoading = ref(false)
const storageLoading = ref(false)
const nodes = ref([])
const storages = ref([])

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showTotal: true,
  showPageSize: true
})

const createFormData = reactive({
  server_id: null,
  node: '',
  vmid: null,
  name: '',
  cores: 1,
  memory: 512,
  disk_size: '10G',
  disk_storage: '',
  network_bridge: 'vmbr0',
  ostype: 'l26',
  iso: '',
  description: ''
})

const createFormRules = {
  server_id: [{ required: true, message: '请选择PVE服务器' }],
  node: [{ required: true, message: '请选择节点' }],
  name: [{ required: true, message: '请输入虚拟机名称' }],
  cores: [{ required: true, message: '请输入CPU核心数' }],
  memory: [{ required: true, message: '请输入内存大小' }],
  disk_size: [{ required: true, message: '请输入磁盘大小' }]
}

const createFormRef = ref(null)

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
    const res = await getVirtualMachines(params)
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
    Message.error('获取虚拟机列表失败：' + (error.message || '未知错误'))
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

const handlePageSizeChange = (pageSize) => {
  pagination.pageSize = pageSize
  pagination.current = 1
  fetchData()
}

const handleCreate = () => {
  createFormVisible.value = true
  Object.assign(createFormData, {
    server_id: null,
    node: '',
    vmid: null,
    name: '',
    cores: 1,
    memory: 512,
    disk_size: '10G',
    disk_storage: '',
    network_bridge: 'vmbr0',
    ostype: 'l26',
    iso: '',
    description: ''
  })
  nodes.value = []
  storages.value = []
}

const handleServerSelect = async (serverId) => {
  if (!serverId) {
    nodes.value = []
    storages.value = []
    createFormData.node = ''
    createFormData.disk_storage = ''
    return
  }
  
  // 清空节点和存储
  createFormData.node = ''
  createFormData.disk_storage = ''
  storages.value = []
  
  nodesLoading.value = true
  try {
    const res = await getPVEServerNodes(serverId)
    nodes.value = Array.isArray(res) ? res : []
  } catch (error) {
    Message.error('获取节点列表失败：' + (error.message || '未知错误'))
    nodes.value = []
  } finally {
    nodesLoading.value = false
  }
}

const handleNodeChange = async (node) => {
  if (!node || !createFormData.server_id) {
    storages.value = []
    createFormData.disk_storage = ''
    return
  }
  
  // 清空存储选择
  createFormData.disk_storage = ''
  
  storageLoading.value = true
  try {
    const res = await getNodeStorage(createFormData.server_id, node)
    storages.value = Array.isArray(res) ? res : []
  } catch (error) {
    Message.error('获取存储列表失败：' + (error.message || '未知错误'))
    storages.value = []
  } finally {
    storageLoading.value = false
  }
}

const handleCreateSubmit = async () => {
  try {
    await createFormRef.value.validate()
    
    await createVirtualMachine(createFormData)
    Message.success('创建虚拟机任务已提交，请稍后查看状态')
    createFormVisible.value = false
    fetchData()
  } catch (error) {
    if (error.errors) {
      return false
    }
    Message.error('创建失败：' + (error.message || '未知错误'))
    return false
  }
}

const handleCreateCancel = () => {
  createFormVisible.value = false
}

const handleVMAction = async (record, action) => {
  const actionMap = {
    start: '启动',
    stop: '停止',
    shutdown: '关闭',
    reboot: '重启'
  }
  
  Modal.confirm({
    title: '确认操作',
    content: `确定要${actionMap[action]}虚拟机 "${record.name}" 吗？`,
    onOk: async () => {
      try {
        await vmAction(record.id, action)
        Message.success(`${actionMap[action]}操作已提交`)
        fetchData()
      } catch (error) {
        Message.error('操作失败：' + (error.message || '未知错误'))
      }
    }
  })
}

const handleSyncStatus = async (record) => {
  try {
    loading.value = true
    await syncVMStatus(record.id)
    Message.success('状态同步成功')
    fetchData()
  } catch (error) {
    Message.error('同步状态失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const handleViewDetail = async (record) => {
  currentVM.value = record
  detailVisible.value = true
}

const handleDelete = (record) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除虚拟机 "${record.name}" (VMID: ${record.vmid}) 吗？此操作不可恢复！`,
    onOk: async () => {
      try {
        await deleteVirtualMachine(record.id)
        Message.success('删除成功')
        fetchData()
      } catch (error) {
        Message.error('删除失败：' + (error.message || '未知错误'))
      }
    }
  })
}

onMounted(() => {
  fetchServers()
  fetchData()
})
</script>

<style scoped>
.virtual-machine {
  padding: 20px;
}

.toolbar {
  margin-bottom: 16px;
}
</style>

