<template>
  <div class="vm-detail-page">
    <div class="vm-detail-toolbar">
      <a-button type="text" class="back-button" @click="handleBack">
        <template #icon>
          <icon-left />
        </template>
        返回列表
      </a-button>
      <div class="vm-detail-header">
        <div class="vm-detail-title">
          <div class="vm-detail-name">{{ currentVM?.name || '虚拟机详情' }}</div>
          <div v-if="currentVM" class="vm-detail-sub">
            VMID {{ currentVM.vmid }} · 节点 {{ currentVM.node || '-' }} · 服务器 {{ currentVM.server_name || '-' }}
          </div>
        </div>
        <div class="vm-detail-actions" v-if="currentVM">
          <a-tag class="status-tag" :color="getStatusColor(currentVM.status)">
            {{ getStatusText(currentVM.status) }}
          </a-tag>
          <a-space>
            <a-button size="small" @click="refreshDetail">刷新</a-button>
            <a-button type="primary" size="small" @click="openCloneModal">
              克隆虚拟机
            </a-button>
          </a-space>
        </div>
      </div>
    </div>

    <a-spin :loading="detailLoading">
      <a-card :bordered="false" class="vm-detail-card">
        <template v-if="currentVM">
          <a-tabs v-model:active-key="detailActiveTab" type="line">
            <a-tab-pane key="overview" title="概览">
              <VMOverviewTab :vm="currentVM" />
            </a-tab-pane>
            <a-tab-pane key="console" title="控制台">
              <VMConsoleTab
                :vm="currentVM"
                :vm-id="vmNumericId"
                :active="detailActiveTab === 'console'"
              />
            </a-tab-pane>
            <a-tab-pane key="hardware" title="硬件">
              <VMHardwareTab
                :vm="currentVM"
                :vm-id="vmNumericId"
                @refresh="refreshDetail"
              />
            </a-tab-pane>
            <a-tab-pane key="backup" title="备份">
              <VMBackupTab
                :vm="currentVM"
                :vm-id="vmNumericId"
              />
            </a-tab-pane>
            <a-tab-pane key="snapshot" title="快照">
              <VMSnapshotTab
                :vm="currentVM"
                :vm-id="vmNumericId"
              />
            </a-tab-pane>
            <a-tab-pane key="tasks" title="任务历史">
              <VMTasksTab
                :vm="currentVM"
                :vm-id="vmNumericId"
              />
            </a-tab-pane>
            <a-tab-pane key="options" title="选项">
              <VMOptionsTab
                :vm="currentVM"
                :vm-id="vmNumericId"
                @refresh="refreshDetail"
              />
            </a-tab-pane>
            <a-tab-pane key="config" title="配置">
              <VMConfigTab :vm="currentVM" />
            </a-tab-pane>
          </a-tabs>
        </template>
        <a-empty v-else description="暂无虚拟机数据" />
      </a-card>
    </a-spin>

    <a-modal
      v-model:visible="cloneVisible"
      title="克隆虚拟机"
      :width="640"
      :ok-loading="cloneSubmitting"
      ok-text="开始克隆"
      @ok="handleCloneSubmit"
      @cancel="handleCloneCancel"
    >
      <a-spin :loading="cloneLoading">
        <a-form :model="cloneForm" layout="vertical">
          <a-form-item label="新虚拟机 ID">
            <div class="clone-vmid-row">
              <a-input-number
                v-model="cloneForm.new_vmid"
                :min="100"
                placeholder="请输入新的 VMID"
              />
              <a-button
                type="outline"
                size="small"
                style="margin-left: 8px;"
                :loading="fetchingNextId"
                @click="fetchNextCloneVMID"
              >
                获取
              </a-button>
            </div>
          </a-form-item>
          <a-form-item label="新虚拟机名称">
            <a-input v-model="cloneForm.name" placeholder="请输入新的虚拟机名称" />
          </a-form-item>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="目标节点">
                <a-select
                  v-model="cloneForm.target_node"
                  placeholder="选择节点"
                  :loading="nodesLoading"
                  allow-clear
                >
                  <a-option
                    v-for="node in cloneNodes"
                    :key="node.node || node.name"
                    :value="node.node || node.name"
                  >
                    {{ node.node || node.name }}
                  </a-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="目标存储（可选）">
                <a-select
                  v-model="cloneForm.storage"
                  placeholder="选择存储"
                  allow-clear
                  :loading="storagesLoading"
                >
                  <a-option
                    v-for="storage in cloneStorages"
                    :key="storage.storage"
                    :value="storage.storage"
                  >
                    {{ storage.storage }} ({{ storage.type }})
                  </a-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="磁盘格式（可选）">
                <a-select v-model="cloneForm.disk_format" allow-clear placeholder="沿用源格式">
                  <a-option value="raw">raw</a-option>
                  <a-option value="qcow2">qcow2</a-option>
                  <a-option value="vmdk">vmdk</a-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="完整克隆">
                <a-switch v-model="cloneForm.full" />
                <template #extra>
                  <span class="field-extra">关闭将创建链接克隆</span>
                </template>
              </a-form-item>
            </a-col>
          </a-row>
          <a-form-item label="描述（可选）">
            <a-textarea
              v-model="cloneForm.description"
              :auto-size="{ minRows: 2, maxRows: 4 }"
              placeholder="为新虚拟机记录备注"
            />
          </a-form-item>
          <a-form-item label="快照名称（可选）">
            <a-input
              v-model="cloneForm.snapname"
              placeholder="指定要克隆的快照名称，不填则使用当前状态"
            />
          </a-form-item>
        </a-form>
      </a-spin>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { IconLeft } from '@arco-design/web-vue/es/icon'
import {
  getVirtualMachine,
  cloneVirtualMachine,
  getPVEServerNodes,
  getNodeStorage,
  getNextVMID
} from '@/api/pve'
import VMOverviewTab from './components/VMOverviewTab.vue'
import VMConsoleTab from './components/VMConsoleTab.vue'
import VMHardwareTab from './components/VMHardwareTab.vue'
import VMConfigTab from './components/VMConfigTab.vue'
import VMBackupTab from './components/VMBackupTab.vue'
import VMSnapshotTab from './components/VMSnapshotTab.vue'
import VMTasksTab from './components/VMTasksTab.vue'
import VMOptionsTab from './components/VMOptionsTab.vue'

const DETAIL_ROUTE_NAME = 'PVEVirtualMachineDetail'

const router = useRouter()
const route = useRoute()

const detailLoading = ref(false)
const detailActiveTab = ref(route.query.tab || 'overview')
const currentVM = ref(null)
const tabSyncing = ref(false)

const cloneVisible = ref(false)
const cloneLoading = ref(false)
const cloneSubmitting = ref(false)
const nodesLoading = ref(false)
const storagesLoading = ref(false)
const fetchingNextId = ref(false)
const cloneNodes = ref([])
const cloneStorages = ref([])
const cloneForm = reactive({
  new_vmid: null,
  name: '',
  target_node: '',
  storage: '',
  disk_format: '',
  full: true,
  description: '',
  snapname: ''
})

const vmId = computed(() => route.params.id)
const vmNumericId = computed(() => {
  if (!vmId.value) return null
  const parsed = Number(vmId.value)
  return Number.isNaN(parsed) ? vmId.value : parsed
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

const resetCloneForm = () => {
  const baseName = currentVM.value?.name ? `${currentVM.value.name}-clone` : ''
  cloneForm.new_vmid = null
  cloneForm.name = baseName
  cloneForm.target_node = currentVM.value?.node || ''
  cloneForm.storage = ''
  cloneForm.disk_format = ''
  cloneForm.full = true
  cloneForm.description = ''
  cloneForm.snapname = ''
}

const fetchCloneNodes = async () => {
  if (!currentVM.value?.server) {
    cloneNodes.value = []
    return
  }
  nodesLoading.value = true
  try {
    const res = await getPVEServerNodes(currentVM.value.server)
    cloneNodes.value = Array.isArray(res) ? res : []
  } catch (error) {
    cloneNodes.value = []
    Message.error('获取节点列表失败：' + (error.message || '未知错误'))
  } finally {
    nodesLoading.value = false
  }
}

const fetchCloneStorages = async (nodeName) => {
  if (!currentVM.value?.server || !nodeName) {
    cloneStorages.value = []
    return
  }
  storagesLoading.value = true
  try {
    const res = await getNodeStorage(currentVM.value.server, nodeName)
    cloneStorages.value = Array.isArray(res) ? res : []
  } catch (error) {
    cloneStorages.value = []
    Message.error('获取存储列表失败：' + (error.message || '未知错误'))
  } finally {
    storagesLoading.value = false
  }
}

const fetchNextCloneVMID = async () => {
  if (!currentVM.value?.server) return
  fetchingNextId.value = true
  try {
    const res = await getNextVMID(currentVM.value.server)
    if (res?.vmid) {
      cloneForm.new_vmid = Number(res.vmid)
    } else if (typeof res === 'number') {
      cloneForm.new_vmid = res
    }
  } catch (error) {
    Message.warning('获取下一个VMID失败，请手动填写')
  } finally {
    fetchingNextId.value = false
  }
}

const prepareCloneModal = async () => {
  if (!currentVM.value) return
  cloneLoading.value = true
  try {
    resetCloneForm()
    await fetchCloneNodes()
    if (!cloneForm.target_node && cloneNodes.value.length > 0) {
      cloneForm.target_node = cloneNodes.value[0].node || cloneNodes.value[0].name || ''
    }
    if (cloneForm.target_node) {
      await fetchCloneStorages(cloneForm.target_node)
    } else {
      cloneStorages.value = []
    }
    await fetchNextCloneVMID()
  } finally {
    cloneLoading.value = false
  }
}

const openCloneModal = () => {
  if (!currentVM.value) {
    Message.warning('暂无虚拟机数据')
    return
  }
  cloneVisible.value = true
  prepareCloneModal()
}

const handleCloneCancel = () => {
  cloneVisible.value = false
}

const handleCloneSubmit = async () => {
  if (!vmId.value) return
  if (!cloneForm.new_vmid) {
    Message.warning('请填写新虚拟机ID')
    return
  }
  if (!cloneForm.name) {
    Message.warning('请填写新虚拟机名称')
    return
  }
  const payload = {
    new_vmid: Number(cloneForm.new_vmid),
    name: cloneForm.name,
    full: !!cloneForm.full,
    target_node: cloneForm.target_node || undefined,
    storage: cloneForm.storage || undefined,
    disk_format: cloneForm.disk_format || undefined,
    description: cloneForm.description || undefined,
    snapname: cloneForm.snapname || undefined
  }
  const cleansed = {}
  Object.entries(payload).forEach(([key, value]) => {
    if (value === '' || value === undefined || value === null) return
    cleansed[key] = value
  })
  cloneSubmitting.value = true
  try {
    await cloneVirtualMachine(vmId.value, cleansed)
    Message.success('克隆任务已提交')
    cloneVisible.value = false
  } catch (error) {
    Message.error('克隆失败：' + (error.message || '未知错误'))
  } finally {
    cloneSubmitting.value = false
  }
}

const loadDetail = async ({ preserveTab = true } = {}) => {
  if (!preserveTab) {
    const routeTab = route.query.tab
    detailActiveTab.value = routeTab ? String(routeTab) : 'overview'
  }
  if (!vmId.value) {
    currentVM.value = null
    return
  }
  detailLoading.value = true
  try {
    const res = await getVirtualMachine(vmId.value)
    currentVM.value = res
  } catch (error) {
    currentVM.value = null
    Message.error('获取虚拟机详情失败：' + (error.message || '未知错误'))
  } finally {
    detailLoading.value = false
  }
}

const refreshDetail = () => {
  loadDetail({ preserveTab: true })
}

const handleBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/pve/vm')
  }
}

watch(
  () => route.query.tab,
  (val) => {
    const tab = val ? String(val) : 'overview'
    if (tab !== detailActiveTab.value) {
      tabSyncing.value = true
      detailActiveTab.value = tab
    }
  }
)

watch(
  () => cloneForm.target_node,
  (val, oldVal) => {
    if (!cloneVisible.value) return
    if (val && val !== oldVal) {
      fetchCloneStorages(val)
    } else if (!val) {
      cloneStorages.value = []
    }
  }
)

watch(detailActiveTab, (val) => {
  if (tabSyncing.value) {
    tabSyncing.value = false
    return
  }
  if (!vmId.value) return
  const routeTab = route.query.tab ? String(route.query.tab) : 'overview'
  if ((val === 'overview' && routeTab === 'overview') || routeTab === val) {
    return
  }
  const newQuery = { ...route.query }
  if (val && val !== 'overview') {
    newQuery.tab = val
  } else {
    delete newQuery.tab
  }
  router.replace({
    name: DETAIL_ROUTE_NAME,
    params: { id: vmId.value },
    query: newQuery
  })
})

watch(
  () => vmId.value,
  (val, oldVal) => {
    if (val && val !== oldVal) {
      loadDetail({ preserveTab: false })
    }
  }
)

onMounted(() => {
  loadDetail({ preserveTab: true })
})
</script>

<style scoped>
.vm-detail-page {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.vm-detail-toolbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.back-button {
  width: fit-content;
  padding-left: 0;
}

.vm-detail-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.vm-detail-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.vm-detail-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.vm-detail-actions .status-tag {
  font-size: 13px;
}

.vm-detail-name {
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-1);
}

.vm-detail-sub {
  color: var(--color-text-3);
  font-size: 13px;
}

.vm-detail-card {
  width: 100%;
}

.clone-vmid-row {
  display: flex;
  align-items: center;
}

.clone-vmid-row :deep(.arco-input-number) {
  flex: 1;
}

.field-extra {
  font-size: 12px;
  color: var(--color-text-3);
}

::v-deep(.arco-tabs) {
  display: flex;
  flex-direction: column;
}

::v-deep(.arco-tabs-content) {
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
}

::v-deep(.arco-tabs-pane) {
  height: 100%;
}
</style>

