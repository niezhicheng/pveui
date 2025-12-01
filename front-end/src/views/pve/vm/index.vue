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
          <a-button
            type="outline"
            :loading="syncing"
            @click="handleSyncAll"
          >
            <template #icon>
              <icon-refresh />
            </template>
            一键同步
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
      @cancel="handleCreateCancel"
      :width="900"
      unmount-on-close
    >
      <a-steps
        :current="currentStep"
        style="margin-bottom: 24px"
      >
        <a-step title="一般设置" />
        <a-step title="操作系统" />
        <a-step title="系统" />
        <a-step title="硬盘" />
        <a-step title="网络" />
        <a-step title="确认" />
      </a-steps>

      <a-form
        ref="createFormRef"
        :model="createFormData"
        :rules="createFormRules"
        layout="vertical"
      >
        <!-- 步骤1: 一般设置 -->
        <div v-show="currentStep === 0">
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

          <a-form-item field="description" label="描述">
            <a-textarea
              v-model="createFormData.description"
              placeholder="请输入虚拟机描述（可选）"
              :auto-size="{ minRows: 2, maxRows: 4 }"
            />
          </a-form-item>
        </div>

        <!-- 步骤2: 操作系统 -->
        <div v-show="currentStep === 1">
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

          <a-form-item field="iso_storage" label="ISO存储（可选）">
            <a-select
              v-model="createFormData.iso_storage"
              placeholder="请选择存储（用于ISO镜像，可选）"
              :loading="storageLoading"
              :disabled="!createFormData.node"
              @change="handleISOStorageChange"
              allow-clear
            >
              <a-option
                v-for="storage in storages"
                :key="storage.storage"
                :value="storage.storage"
              >
                {{ storage.storage }} ({{ storage.type }})
              </a-option>
            </a-select>
            <template #extra>
              <span style="color: var(--color-text-3); font-size: 12px;">
                仅在选择ISO镜像时需要
              </span>
            </template>
          </a-form-item>

          <a-form-item field="iso" label="ISO镜像（可选）">
            <a-select
              v-model="createFormData.iso"
              placeholder="请选择ISO镜像或留空"
              :loading="isoLoading"
              :disabled="!createFormData.iso_storage"
              allow-clear
              allow-search
            >
              <a-option
                v-for="iso in isoList"
                :key="iso.volid"
                :value="iso.volid"
              >
                {{ iso.volid }}
              </a-option>
            </a-select>
            <template #extra>
              <span style="color: var(--color-text-3); font-size: 12px;">
                如果不选择ISO镜像，将创建一个空虚拟机
              </span>
            </template>
          </a-form-item>
        </div>

        <!-- 步骤3: 系统 -->
        <div v-show="currentStep === 2">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item field="sockets" label="CPU Sockets">
                <a-input-number
                  v-model="createFormData.sockets"
                  :min="1"
                  :max="8"
                  placeholder="默认1"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item field="cores" label="每Socket核心数">
                <a-input-number
                  v-model="createFormData.cores"
                  :min="1"
                  :max="32"
                  placeholder="默认1"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item field="cpu" label="CPU类型">
            <a-select
              v-model="createFormData.cpu"
              placeholder="请选择CPU类型"
              allow-search
            >
              <a-option value="host">host（主机CPU）</a-option>
              <a-option value="x86-64-v2-AES">x86-64-v2-AES</a-option>
              <a-option value="x86-64-v3">x86-64-v3</a-option>
              <a-option value="x86-64-v4">x86-64-v4</a-option>
              <a-option value="kvm64">kvm64</a-option>
              <a-option value="qemu64">qemu64</a-option>
            </a-select>
            <template #extra>
              <span style="color: var(--color-text-3); font-size: 12px;">
                总CPU核心数 = Sockets × 每Socket核心数
              </span>
            </template>
          </a-form-item>

          <a-form-item field="memory" label="内存(MB)">
            <a-input-number
              v-model="createFormData.memory"
              :min="512"
              :step="512"
              placeholder="默认512"
              style="width: 100%"
            />
            <template #extra>
              <span style="color: var(--color-text-3); font-size: 12px;">
                建议值：512MB, 1024MB, 2048MB, 4096MB等
              </span>
            </template>
          </a-form-item>

          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item field="scsihw" label="SCSI硬件类型">
                <a-select
                  v-model="createFormData.scsihw"
                  placeholder="请选择SCSI硬件类型"
                >
                  <a-option value="virtio-scsi-single">virtio-scsi-single</a-option>
                  <a-option value="virtio-scsi-pci">virtio-scsi-pci</a-option>
                  <a-option value="lsi">lsi</a-option>
                  <a-option value="lsi53c810">lsi53c810</a-option>
                  <a-option value="megasas">megasas</a-option>
                  <a-option value="pvscsi">pvscsi</a-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item field="numa" label="NUMA">
                <a-switch v-model="createFormData.numa" />
                <template #extra>
                  <span style="color: var(--color-text-3); font-size: 12px;">
                    启用NUMA（非统一内存访问）
                  </span>
                </template>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 步骤4: 硬盘 -->
        <div v-show="currentStep === 3">
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

          <a-form-item field="disk_size" label="磁盘大小 (GB)">
            <a-input-number
              v-model="createFormData.disk_size"
              :min="1"
              placeholder="请输入数字，例如：10"
            />
            <template #extra>
              <span style="color: var(--color-text-3); font-size: 12px;">
                直接填写数字，单位为GB（例如：10 表示 10GB）
              </span>
            </template>
          </a-form-item>
        </div>

        <!-- 步骤5: 网络 -->
        <div v-show="currentStep === 4">
          <a-form-item field="network_bridge" label="网络桥接">
            <a-input
              v-model="createFormData.network_bridge"
              placeholder="默认vmbr0"
            />
            <template #extra>
              <span style="color: var(--color-text-3); font-size: 12px;">
                通常使用vmbr0，根据您的网络配置调整
              </span>
            </template>
          </a-form-item>

          <a-form-item field="network_firewall" label="防火墙">
            <a-switch v-model="createFormData.network_firewall" />
            <template #extra>
              <span style="color: var(--color-text-3); font-size: 12px;">
                启用防火墙规则
              </span>
            </template>
          </a-form-item>
        </div>

        <!-- 步骤6: 确认 -->
        <div v-show="currentStep === 5">
          <a-descriptions
            :column="1"
            bordered
            :data="summaryData"
          />
        </div>
      </a-form>

      <template #footer>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <a-button v-if="currentStep > 0" @click="handlePrevStep">上一步</a-button>
          <span v-else></span>
          <div>
            <a-button @click="handleCreateCancel" style="margin-right: 8px;">取消</a-button>
            <a-button
              v-if="currentStep < 5"
              type="primary"
              @click="handleNextStep"
            >
              下一步
            </a-button>
            <a-button
              v-else
              type="primary"
              @click="handleCreateSubmit"
              :loading="submitting"
            >
              创建
            </a-button>
          </div>
        </div>
      </template>
    </a-modal>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Message, Modal } from '@arco-design/web-vue'
import { IconPlus, IconDown, IconRefresh } from '@arco-design/web-vue/es/icon'
import {
  getPVEServers,
  getPVEServerNodes,
  getNodeStorage,
  getStorageISO,
  getNextVMID,
  getVirtualMachines,
  createVirtualMachine,
  deleteVirtualMachine,
  vmAction,
  syncVMStatus,
  syncAllVirtualMachines
} from '@/api/pve'

const VM_DETAIL_ROUTE_NAME = 'PVEVirtualMachineDetail'

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

const router = useRouter()

const loading = ref(false)
const searchText = ref('')
const selectedServer = ref(null)
const tableData = ref([])
const servers = ref([])
const createFormVisible = ref(false)
const nodesLoading = ref(false)
const storageLoading = ref(false)
const isoLoading = ref(false)
const nodes = ref([])
const storages = ref([])
const isoList = ref([])
const currentStep = ref(0)
const submitting = ref(false)
const syncing = ref(false)

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
  sockets: 1,
  cores: 1,
  cpu: 'x86-64-v2-AES',
  memory: 512,
  scsihw: 'virtio-scsi-single',
  numa: false,
  disk_size: 10,
  disk_storage: '',
  iso_storage: '', // ISO存储（可选）
  network_bridge: 'vmbr0',
  network_firewall: true,
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
  disk_size: [{ required: true, message: '请输入磁盘大小（GB）' }],
  disk_storage: [{ required: true, message: '请选择存储' }]
}

// 计算属性：确认页面的摘要数据
const summaryData = computed(() => {
  const server = servers.value.find(s => s.id === createFormData.server_id)
  return [
    { label: 'PVE服务器', value: server?.name || '-' },
    { label: '节点', value: createFormData.node || '-' },
    { label: '虚拟机ID', value: createFormData.vmid || '自动分配' },
    { label: '虚拟机名称', value: createFormData.name || '-' },
    { label: '描述', value: createFormData.description || '无' },
    { label: '操作系统类型', value: getOSTypeText(createFormData.ostype) },
    { label: 'ISO存储', value: createFormData.iso_storage || '无' },
    { label: 'ISO镜像', value: createFormData.iso || '无' },
    { label: 'CPU Sockets', value: createFormData.sockets || '-' },
    { label: '每Socket核心数', value: createFormData.cores || '-' },
    { label: '总CPU核心数', value: (createFormData.sockets || 1) * (createFormData.cores || 1) },
    { label: 'CPU类型', value: createFormData.cpu || '-' },
    { label: '内存', value: `${createFormData.memory || '-'} MB` },
    { label: 'SCSI硬件类型', value: createFormData.scsihw || '-' },
    { label: 'NUMA', value: createFormData.numa ? '启用' : '禁用' },
    { label: '存储', value: createFormData.disk_storage || '-' },
    { label: '磁盘大小', value: createFormData.disk_size ? `${createFormData.disk_size} GB` : '-' },
    { label: '网络桥接', value: createFormData.network_bridge || '-' },
    { label: '防火墙', value: createFormData.network_firewall ? '启用' : '禁用' }
  ]
})

const getOSTypeText = (ostype) => {
  const map = {
    'l26': 'Linux 2.6+',
    'l24': 'Linux 2.4',
    'w2k': 'Windows 2000',
    'w2k3': 'Windows 2003',
    'w2k8': 'Windows 2008',
    'wvista': 'Windows Vista',
    'win7': 'Windows 7',
    'win8': 'Windows 8',
    'win10': 'Windows 10',
    'win11': 'Windows 11',
    'other': '其他'
  }
  return map[ostype] || ostype
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
  currentStep.value = 0
  Object.assign(createFormData, {
    server_id: null,
    node: '',
    vmid: null,
    name: '',
    sockets: 1,
    cores: 1,
    cpu: 'x86-64-v2-AES',
    memory: 512,
    scsihw: 'virtio-scsi-single',
    numa: false,
    disk_size: 10,
    disk_storage: '',
    iso_storage: '',
    network_bridge: 'vmbr0',
    network_firewall: true,
    ostype: 'l26',
    iso: '',
    description: ''
  })
  nodes.value = []
  storages.value = []
  isoList.value = []
}

const handleServerSelect = async (serverId) => {
  if (!serverId) {
    nodes.value = []
    storages.value = []
    createFormData.node = ''
    createFormData.disk_storage = ''
    createFormData.iso_storage = ''
    isoList.value = []
    createFormData.iso = ''
    return
  }
  
  // 清空节点和存储
  createFormData.node = ''
  createFormData.disk_storage = ''
  createFormData.iso_storage = ''
  storages.value = []
  isoList.value = []
  createFormData.iso = ''
  
  // 如果还没有VMID，尝试获取下一个可用的VMID
  if (!createFormData.vmid) {
    try {
      const res = await getNextVMID(serverId)
      if (res && res.vmid) {
        createFormData.vmid = res.vmid
      }
    } catch (error) {
      // 获取VMID失败不影响继续操作，用户仍可手动输入
      console.warn('获取下一个VMID失败：', error)
    }
  }
  
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
    createFormData.iso_storage = ''
    isoList.value = []
    createFormData.iso = ''
    return
  }
  
  // 清空存储选择
  createFormData.disk_storage = ''
  createFormData.iso_storage = ''
  isoList.value = []
  createFormData.iso = ''
  
  // 自动获取下一个可用的VMID
  if (!createFormData.vmid) {
    try {
      const res = await getNextVMID(createFormData.server_id)
      if (res && res.vmid) {
        createFormData.vmid = res.vmid
      }
    } catch (error) {
      // 获取VMID失败不影响继续操作，用户仍可手动输入
      console.warn('获取下一个VMID失败：', error)
    }
  }
  
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

const handleISOStorageChange = async (storage) => {
  // 如果清空存储，也清空ISO选择
  if (!storage) {
    isoList.value = []
    createFormData.iso = ''
    return
  }
  
  if (!createFormData.node || !createFormData.server_id) {
    isoList.value = []
    createFormData.iso = ''
    return
  }
  
  isoLoading.value = true
  try {
    const res = await getStorageISO(createFormData.server_id, createFormData.node, storage)
    isoList.value = Array.isArray(res) ? res : []
    // 如果之前选择的ISO不在新列表中，清空ISO选择
    if (createFormData.iso && !isoList.value.find(iso => iso.volid === createFormData.iso)) {
      createFormData.iso = ''
    }
  } catch (error) {
    // ISO列表获取失败不影响创建，只记录错误
    console.warn('获取ISO镜像列表失败：', error)
    isoList.value = []
    createFormData.iso = ''
  } finally {
    isoLoading.value = false
  }
}

// 步骤验证规则
const stepValidationRules = {
  0: ['server_id', 'node', 'name'], // 一般设置
  1: ['ostype'], // 操作系统（ISO可选）
  2: ['sockets', 'cores', 'memory', 'cpu', 'scsihw'], // 系统
  3: ['disk_storage', 'disk_size'], // 硬盘
  4: ['network_bridge'], // 网络
  5: [] // 确认（无需验证）
}

const handleNextStep = async () => {
  try {
    // 验证当前步骤的必填字段
    const fieldsToValidate = stepValidationRules[currentStep.value]
    if (fieldsToValidate && fieldsToValidate.length > 0) {
      await createFormRef.value.validate(fieldsToValidate)
    }
    
    // 特殊处理：如果选择了ISO，需要确保选择了ISO存储
    if (currentStep.value === 1 && createFormData.iso && !createFormData.iso_storage) {
      Message.warning('选择ISO镜像需要先选择ISO存储')
      return
    }
    
    if (currentStep.value < 5) {
      currentStep.value++
    }
  } catch (error) {
    // 验证失败，不进入下一步
    if (error.errors) {
      return
    }
  }
}

const handlePrevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const handleCreateSubmit = async () => {
  try {
    submitting.value = true
    
    // 最终验证所有必填字段
    const allRequiredFields = ['server_id', 'node', 'name', 'cores', 'memory', 'disk_size', 'disk_storage', 'network_bridge']
    await createFormRef.value.validate(allRequiredFields)
    
    // 准备提交数据，如果vmid为null或undefined，则不包含该字段
    const submitData = { ...createFormData }
    if (submitData.vmid === null || submitData.vmid === undefined) {
      delete submitData.vmid
    }
    
    await createVirtualMachine(submitData)
    Message.success('创建虚拟机任务已提交，请稍后查看状态')
    createFormVisible.value = false
    currentStep.value = 0
    fetchData()
  } catch (error) {
    if (error.errors) {
      return
    }
    Message.error('创建失败：' + (error.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

const handleCreateCancel = () => {
  createFormVisible.value = false
  currentStep.value = 0
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

const handleViewDetail = (record) => {
  if (!record || !record.id) return
  router.push({
    name: VM_DETAIL_ROUTE_NAME,
    params: { id: record.id }
  })
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

const handleSyncAll = async () => {
  if (!servers.value.length) {
    Message.warning('请先添加至少一个 PVE 服务器')
    return
  }
  if (syncing.value) return
  syncing.value = true
  try {
    const payload = {}
    if (selectedServer.value) {
      payload.server_id = selectedServer.value
    }
    const res = await syncAllVirtualMachines(payload)
    Message.success(`同步完成，新增 ${res?.created ?? 0} 台，更新 ${res?.updated ?? 0} 台`)
    fetchData()
  } catch (error) {
    Message.error('同步失败：' + (error.message || '未知错误'))
  } finally {
    syncing.value = false
  }
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

