<template>
  <a-modal
    v-model:visible="visibleProxy"
    title="虚拟机详情"
    :footer="false"
    :width="detailModalWidth"
    unmount-on-close
  >
    <a-spin :loading="detailLoading">
      <div v-if="currentVM" class="vm-detail">
        <div class="vm-detail-header">
          <div>
            <div class="vm-detail-name">{{ currentVM.name }}</div>
            <div class="vm-detail-sub">
              VMID {{ currentVM.vmid }} · 节点 {{ currentVM.node || '-' }} · 服务器 {{ currentVM.server_name || '-' }}
            </div>
          </div>
          <div class="vm-detail-status">
            <a-tag :color="getStatusColor(currentVM.status)">
              {{ getStatusText(currentVM.status) }}
            </a-tag>
          </div>
        </div>

        <a-tabs v-model:active-key="detailActiveTab">
          <a-tab-pane key="overview" title="概览">
            <a-row :gutter="16">
              <a-col :span="12">
                <a-card title="基本信息" :bordered="false">
                  <a-descriptions :column="1" bordered :data="detailOverviewData.basic" />
                </a-card>
              </a-col>
              <a-col :span="12">
                <a-card title="资源" :bordered="false">
                  <a-descriptions :column="1" bordered :data="detailOverviewData.resource" />
                </a-card>
              </a-col>
            </a-row>
            <a-card title="时间与状态" :bordered="false" style="margin-top: 16px;">
              <a-descriptions :column="2" bordered :data="detailOverviewData.meta" />
            </a-card>
          </a-tab-pane>
          <a-tab-pane key="console" title="控制台">
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
                  id="noVNC_container"
                  class="novnc-container"
                  :style="{ display: consoleLoading || consoleError ? 'none' : 'flex' }"
                ></div>
              </div>
            </a-card>
          </a-tab-pane>
          <a-tab-pane key="hardware" title="硬件">
            <a-card :bordered="false">
              <div class="hardware-toolbar">
                <a-dropdown trigger="click">
                  <a-button type="primary" size="small">
                    添加硬件
                    <icon-down />
                  </a-button>
                  <template #content>
                    <a-doption
                      v-for="option in hardwareAddOptions"
                      :key="option.type"
                      @click="openAddHardwareDialog(option.type)"
                    >
                      {{ option.label }}
                    </a-doption>
                  </template>
                </a-dropdown>
              </div>
              <a-table
                :columns="hardwareColumns"
                :data="hardwareRows"
                :pagination="false"
                size="small"
              >
                <template #value="{ record }">
                  <div class="hardware-value">{{ record.value }}</div>
                </template>
                <template #actions="{ record }">
                  <a-button
                    v-if="record.editable"
                    type="text"
                    size="small"
                    @click="openEditDialog(record.key)"
                  >
                    编辑
                  </a-button>
                </template>
              </a-table>
            </a-card>
          </a-tab-pane>
          <a-tab-pane key="config" title="配置">
            <a-card :bordered="false">
              <a-empty v-if="!configEntries.length" description="暂无配置数据" />
              <a-descriptions v-else :column="1" bordered>
                <a-descriptions-item
                  v-for="item in configEntries"
                  :key="item.label"
                  :label="item.label"
                >
                  <pre class="config-pre">{{ item.value }}</pre>
                </a-descriptions-item>
              </a-descriptions>
            </a-card>
          </a-tab-pane>
        </a-tabs>
      </div>
      <a-empty v-else description="暂无虚拟机数据" />
    </a-spin>
  </a-modal>

  <a-modal
    v-model:visible="editState.visible"
    :title="editState.title"
    :footer="false"
    :width="520"
    unmount-on-close
  >
    <a-form
      ref="editFormRef"
      :model="editForm"
      :rules="editFormRules"
      label-align="left"
      label-col="{ span: 7 }"
      wrapper-col="{ span: 17 }"
      layout="horizontal"
    >
      <template v-if="editState.type === 'cpu'">
        <a-form-item field="sockets" label="CPU Sockets">
          <a-input-number v-model="editForm.sockets" :min="1" :max="8" />
        </a-form-item>
        <a-form-item field="cores" label="每Socket核心">
          <a-input-number v-model="editForm.cores" :min="1" :max="64" />
        </a-form-item>
        <a-form-item field="cpu" label="CPU类型">
          <a-select v-model="editForm.cpu" allow-search>
            <a-option v-for="option in cpuOptions" :key="option" :value="option">
              {{ option }}
            </a-option>
          </a-select>
        </a-form-item>
        <a-form-item field="numa" label="NUMA">
          <a-switch v-model="editForm.numa" />
        </a-form-item>
      </template>
      <template v-else-if="editState.type === 'memory'">
        <a-form-item field="memory" label="内存(MB)">
          <a-input-number v-model="editForm.memory" :min="256" :step="256" />
        </a-form-item>
      </template>
      <template v-else-if="editState.type === 'disk'">
        <a-form-item field="scsi0" label="磁盘(scsi0)">
          <a-input v-model="editForm.scsi0" placeholder="示例：local-lvm:32" />
          <template #extra>
            直接使用PVE格式，支持 local-lvm:32、ceph-pool:32 等
          </template>
        </a-form-item>
      </template>
      <template v-else-if="editState.type === 'network'">
        <a-form-item field="net0" label="网络(net0)">
          <a-input
            v-model="editForm.net0"
            placeholder="示例：virtio,bridge=vmbr0,firewall=1"
          />
        </a-form-item>
      </template>
    </a-form>

    <div class="edit-footer">
      <a-button @click="handleEditCancel" style="margin-right: 12px;">取消</a-button>
      <a-button type="primary" :loading="editState.submitting" @click="handleEditSubmit">
        保存
      </a-button>
    </div>
  </a-modal>

  <!-- 添加硬盘 -->
  <a-modal
    v-model:visible="addState.visible"
    :title="addState.title"
    :footer="false"
    :width="560"
    unmount-on-close
  >
    <a-form
      ref="addFormRef"
      :model="addForm"
      :rules="addFormRules"
      layout="vertical"
    >
      <template v-if="addState.type === 'disk'">
        <a-form-item field="storage" label="存储">
          <a-select
            v-model="addForm.storage"
            :loading="storagesLoading"
            placeholder="请选择存储"
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
        <a-form-item field="size" label="容量(GB)">
          <a-input-number v-model="addForm.size" :min="1" />
        </a-form-item>
        <a-form-item field="iothread" label="启用IO Thread">
          <a-switch v-model="addForm.iothread" />
        </a-form-item>
      </template>
      <template v-else-if="addState.type === 'cdrom'">
        <a-form-item field="isoStorage" label="ISO存储">
          <a-select
            v-model="addForm.isoStorage"
            :loading="storagesLoading"
            @change="handleISOStorageChange"
          >
            <a-option
              v-for="storage in isoStorages"
              :key="storage.storage"
              :value="storage.storage"
            >
              {{ storage.storage }}
            </a-option>
          </a-select>
        </a-form-item>
        <a-form-item field="iso" label="ISO镜像">
          <a-select
            v-model="addForm.iso"
            :loading="isoLoading"
          >
            <a-option
              v-for="iso in isoList"
              :key="iso.volid"
              :value="iso.volid"
            >
              {{ iso.volid }}
            </a-option>
          </a-select>
        </a-form-item>
      </template>
      <template v-else-if="addState.type === 'network'">
        <a-form-item field="model" label="网卡模型">
          <a-select v-model="addForm.model">
            <a-option value="virtio">virtio</a-option>
            <a-option value="e1000">e1000</a-option>
            <a-option value="vmxnet3">vmxnet3</a-option>
            <a-option value="rtl8139">rtl8139</a-option>
          </a-select>
        </a-form-item>
        <a-form-item field="bridge" label="桥接">
          <a-select
            v-model="addForm.bridge"
            :loading="networksLoading"
            allow-search
          >
            <a-option
              v-for="bridge in bridgeOptions"
              :key="bridge"
              :value="bridge"
            >
              {{ bridge }}
            </a-option>
          </a-select>
        </a-form-item>
        <a-form-item field="macaddr" label="MAC地址 (可选)">
          <a-input v-model="addForm.macaddr" placeholder="示例：DE:AD:BE:EF:12:34" />
        </a-form-item>
        <a-form-item field="firewall" label="启用防火墙">
          <a-switch v-model="addForm.firewall" />
        </a-form-item>
      </template>
      <template v-else-if="addState.type === 'efi'">
        <a-form-item field="storage" label="EFI存储">
          <a-select v-model="addForm.storage" :loading="storagesLoading">
            <a-option
              v-for="storage in storages"
              :key="storage.storage"
              :value="storage.storage"
            >
              {{ storage.storage }}
            </a-option>
          </a-select>
        </a-form-item>
        <a-form-item field="efitype" label="EFI类型">
          <a-select v-model="addForm.efitype">
            <a-option value="4m">4M (默认)</a-option>
            <a-option value="2m">2M</a-option>
          </a-select>
        </a-form-item>
        <a-form-item field="pre_enrolled" label="预置微软密钥">
          <a-switch v-model="addForm.pre_enrolled" />
        </a-form-item>
      </template>
      <template v-else-if="addState.type === 'tpm'">
        <a-form-item field="storage" label="TPM存储">
          <a-select v-model="addForm.storage" :loading="storagesLoading">
            <a-option
              v-for="storage in storages"
              :key="storage.storage"
              :value="storage.storage"
            >
              {{ storage.storage }}
            </a-option>
          </a-select>
        </a-form-item>
        <a-form-item field="version" label="版本">
          <a-select v-model="addForm.version">
            <a-option value="v2.0">v2.0</a-option>
            <a-option value="v1.2">v1.2</a-option>
          </a-select>
        </a-form-item>
        <a-form-item field="model" label="模型">
          <a-select v-model="addForm.model">
            <a-option value="tpm-crb">tpm-crb</a-option>
            <a-option value="tpm-tis">tpm-tis</a-option>
          </a-select>
        </a-form-item>
      </template>
      <template v-else-if="addState.type === 'usb'">
        <a-form-item field="host" label="主机设备 (Vendor:Product)">
          <a-input v-model="addForm.host" placeholder="示例：1234:abcd" />
        </a-form-item>
        <a-form-item field="usb3" label="USB3">
          <a-switch v-model="addForm.usb3" />
        </a-form-item>
      </template>
      <template v-else-if="addState.type === 'pci'">
        <a-form-item field="host" label="PCI设备 (Domain:Bus:Slot.Func)">
          <a-input v-model="addForm.host" placeholder="示例：0000:00:14.0" />
        </a-form-item>
        <a-form-item field="pcie" label="启用PCIE">
          <a-switch v-model="addForm.pcie" />
        </a-form-item>
      </template>
      <template v-else-if="addState.type === 'serial'">
        <a-form-item field="mode" label="模式">
          <a-select v-model="addForm.mode">
            <a-option value="socket">socket</a-option>
            <a-option value="server">server</a-option>
            <a-option value="telnet">telnet</a-option>
            <a-option value="pipe">pipe</a-option>
          </a-select>
        </a-form-item>
        <a-form-item field="path" label="路径/端口 (可选)">
          <a-input v-model="addForm.path" placeholder="示例：/var/run/qemu-server/serial0" />
        </a-form-item>
      </template>
      <template v-else-if="addState.type === 'cloudinit'">
        <a-alert type="warning" style="margin-bottom: 12px;">
          CloudInit 会自动创建配置盘，如已有 ide2 设备请先移除。
        </a-alert>
        <a-form-item field="storage" label="存储">
          <a-select v-model="addForm.storage" :loading="storagesLoading">
            <a-option
              v-for="storage in storages"
              :key="storage.storage"
              :value="storage.storage"
            >
              {{ storage.storage }}
            </a-option>
          </a-select>
        </a-form-item>
        <a-form-item field="ciuser" label="默认用户">
          <a-input v-model="addForm.ciuser" />
        </a-form-item>
        <a-form-item field="cipassword" label="密码">
          <a-input-password v-model="addForm.cipassword" />
        </a-form-item>
        <a-form-item field="ipconfig0" label="IP配置 (可选)">
          <a-input v-model="addForm.ipconfig0" placeholder="示例：ip=dhcp 或 ip=192.168.1.10/24,gw=192.168.1.1" />
        </a-form-item>
      </template>
      <template v-else-if="addState.type === 'audio'">
        <a-form-item field="device" label="音频设备">
          <a-select v-model="addForm.device">
            <a-option value="ich9-intel-hda">ich9-intel-hda</a-option>
            <a-option value="intel-hda">intel-hda</a-option>
            <a-option value="ac97">ac97</a-option>
          </a-select>
        </a-form-item>
        <a-form-item field="driver" label="驱动">
          <a-select v-model="addForm.driver">
            <a-option value="spice">spice</a-option>
            <a-option value="none">none</a-option>
          </a-select>
        </a-form-item>
      </template>
      <template v-else-if="addState.type === 'rng'">
        <a-form-item field="source" label="随机源">
          <a-input v-model="addForm.source" placeholder="/dev/urandom" />
        </a-form-item>
      </template>
      <template v-else-if="addState.type === 'virtiofs'">
        <a-form-item field="tag" label="Mount Tag">
          <a-input v-model="addForm.tag" />
        </a-form-item>
        <a-form-item field="path" label="主机路径">
          <a-input v-model="addForm.path" />
        </a-form-item>
      </template>
    </a-form>
    <div class="edit-footer">
      <a-button @click="handleAddCancel" style="margin-right: 12px;">取消</a-button>
      <a-button type="primary" :loading="addState.submitting" @click="handleAddSubmit">
        添加
      </a-button>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, reactive, watch, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconDown } from '@arco-design/web-vue/es/icon'
import {
  getVirtualMachine,
  updateVirtualMachineHardware,
  getNodeStorage,
  getNodeNetwork,
  getStorageISO,
  createVMConsoleSession
} from '@/api/pve'
import RFB from '@novnc/novnc/core/rfb'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  vmId: {
    type: [Number, String],
    default: null
  },
  fallbackRecord: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible'])

const visibleProxy = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

 const detailLoading = ref(false)
 const detailActiveTab = ref('overview')
 const detailModalWidth = ref(960)
 const currentVM = ref(null)
 const editFormRef = ref(null)
 const addFormRef = ref(null)
const novncContainer = ref(null)
const consoleLoading = ref(false)
const consoleError = ref('')
const rfb = ref(null)

 const editState = reactive({
   visible: false,
   type: '',
   title: '',
   submitting: false
 })

const editForm = reactive({})
const addState = reactive({
  visible: false,
  type: '',
  title: '',
  submitting: false
})
 const addForm = reactive({})

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
  if (!currentVM.value) return

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
    const session = await createVMConsoleSession(currentVM.value.id, { type: 'novnc' })
    if (!session?.session_token) {
      throw new Error('未获取到控制台会话信息')
    }

    // 优先使用 proxy_url（完整的 WebSocket URL），如果没有则使用 proxy_path 构建
    let wsUrl = ''
    if (session.proxy_url) {
      // 直接使用后端返回的完整 WebSocket URL
      wsUrl = session.proxy_url
    } else if (session.proxy_path) {
      // 使用 proxy_path 构建完整的 WebSocket URL
      const baseUrl = buildBackendUrl('')
      const wsProtocol = baseUrl.startsWith('https') ? 'wss' : 'ws'
      const wsHost = baseUrl.replace(/^https?:\/\//, '').replace(/\/$/, '')
      wsUrl = `${wsProtocol}://${wsHost}${session.proxy_path.startsWith('/') ? session.proxy_path : '/' + session.proxy_path}`
    } else {
      throw new Error('未获取到 WebSocket 代理路径')
    }

    // 使用 password 字段作为 VNC 密码
    const password = session.password || ''

    console.log('连接 noVNC:', {
      wsUrl,
      hasPassword: !!password,
      vmid: session.vmid,
      node: session.node
    })

    // 等待 DOM 更新，确保 novncContainer 元素已经渲染
    await nextTick()

    // 获取容器元素（优先使用 ref，如果不存在则通过 ID 获取）
    const container = novncContainer.value || document.getElementById('noVNC_container')
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
    // scaleViewport: true 表示本地缩放，canvas 会缩放以适应容器，保持宽高比
    // resizeSession: false 表示不调整远程会话大小，只进行本地缩放
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
      // 连接成功后，触发一次 resize 以确保正确布局和居中
      setTimeout(() => {
        if (rfb.value && container) {
          // 触发容器 resize 事件，让 noVNC 重新计算布局
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

const storages = ref([])
const storagesLoading = ref(false)
const networks = ref([])
const networksLoading = ref(false)
const isoStorages = ref([])
const isoList = ref([])
const isoLoading = ref(false)

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

const detailOverviewData = computed(() => {
  const vm = currentVM.value
  if (!vm) {
    return { basic: [], resource: [], meta: [] }
  }
  return {
    basic: [
      { label: '虚拟机ID', value: vm.vmid || '-' },
      { label: '节点', value: vm.node || '-' },
      { label: '所属服务器', value: vm.server_name || '-' },
      { label: '描述', value: vm.description || '无' }
    ],
    resource: [
      { label: 'CPU核心数', value: vm.cpu_cores ? `${vm.cpu_cores} vCPU` : '-' },
      { label: '内存', value: vm.memory_mb ? `${vm.memory_mb} MB` : '-' },
      { label: '磁盘', value: vm.disk_gb ? `${vm.disk_gb} GB` : '-' },
      { label: 'IP地址', value: vm.ip_address || '未分配' }
    ],
    meta: [
      { label: '创建时间', value: vm.created_at || '-' },
      { label: '更新时间', value: vm.updated_at || '-' },
      { label: '状态', value: getStatusText(vm.status) }
    ]
  }
})

const configEntries = computed(() => {
  const config = currentVM.value?.pve_config || {}
  return Object.keys(config).map(key => ({
    label: key,
    value: typeof config[key] === 'object' ? JSON.stringify(config[key], null, 2) : String(config[key])
  }))
})

const hardwareAddOptions = [
  { type: 'disk', label: '硬盘' },
  { type: 'cdrom', label: 'CD/DVD 驱动器' },
  { type: 'network', label: '网络设备' },
  { type: 'efi', label: 'EFI 磁盘' },
  { type: 'tpm', label: 'TPM 状态' },
  { type: 'usb', label: 'USB 设备' },
  { type: 'pci', label: 'PCI 设备' },
  { type: 'serial', label: '串行端口' },
  { type: 'cloudinit', label: 'CloudInit 设备' },
  { type: 'audio', label: '音频设备' },
  { type: 'rng', label: 'VirtIO RNG' },
  { type: 'virtiofs', label: 'Virtiofs' }
]

const hardwareColumns = [
  { title: '硬件', dataIndex: 'label', width: 160 },
  { title: '参数', dataIndex: 'value', slotName: 'value' },
  { title: '操作', dataIndex: 'actions', slotName: 'actions', width: 100 }
]

const hardwareRows = computed(() => {
  const vm = currentVM.value
  if (!vm) {
    return []
  }
  const config = vm.pve_config || {}
  const rows = []
  const sockets = Number(config.sockets || 1)
  const coresPerSocket = Number(config.cores || (vm.cpu_cores ? Math.max(1, Math.floor(vm.cpu_cores / (sockets || 1))) : 1))
  const cpuType = config.cpu || '默认'
  rows.push({
    key: 'cpu',
    label: '处理器',
    value: `${sockets} Socket × ${coresPerSocket} Core (CPU: ${cpuType})`,
    editable: true
  })
  rows.push({
    key: 'memory',
    label: '内存',
    value: config.memory ? `${config.memory} MB` : vm.memory_mb ? `${vm.memory_mb} MB` : '-',
    editable: true
  })

  Object.keys(config).forEach((key) => {
    if (/^scsi\d+$/.test(key)) {
      rows.push({
        key,
        label: `磁盘 (${key})`,
        value: config[key],
        editable: key === 'scsi0'
      })
    } else if (/^ide\d+$/.test(key)) {
      rows.push({
        key,
        label: `IDE设备 (${key})`,
        value: config[key],
        editable: key === 'ide2'
      })
    } else if (/^net\d+$/.test(key)) {
      rows.push({
        key,
        label: `网络 (${key})`,
        value: config[key],
        editable: key === 'net0'
      })
    }
  })

  if (config.efidisk0) {
    rows.push({ key: 'efidisk0', label: 'EFI 磁盘', value: config.efidisk0, editable: false })
  }
  if (config.tpmstate0) {
    rows.push({ key: 'tpmstate0', label: 'TPM', value: config.tpmstate0, editable: false })
  }
  if (config.usb0) {
    rows.push({ key: 'usb0', label: 'USB 设备', value: config.usb0, editable: false })
  }
  if (config.hostpci0) {
    rows.push({ key: 'hostpci0', label: 'PCI 设备', value: config.hostpci0, editable: false })
  }
  if (config.serial0) rows.push({ key: 'serial0', label: '串口', value: config.serial0, editable: false })
  if (config.audio0) rows.push({ key: 'audio0', label: '音频', value: config.audio0, editable: false })
  if (config.rng0) rows.push({ key: 'rng0', label: '随机数设备', value: config.rng0, editable: false })
  if (config.virtiofs0) rows.push({ key: 'virtiofs0', label: 'Virtiofs', value: config.virtiofs0, editable: false })

  return rows
})

const cpuOptions = [
  'host',
  'x86-64-v2-AES',
  'x86-64-v3',
  'x86-64-v4',
  'kvm64',
  'qemu64'
]

const bridgeOptions = computed(() => {
  const bridges = networks.value
    .filter(item => item.type === 'bridge' && item.iface)
    .map(item => item.iface)
  const unique = Array.from(new Set(bridges))
  if (!unique.includes('vmbr0')) {
    unique.push('vmbr0')
  }
  return unique
})

const updateDetailWidth = () => {
  const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 1200
  // 增加控制台模态框的宽度，以便更好地显示 VNC 画面
  detailModalWidth.value = Math.max(Math.min(viewportWidth - 80, 1600), 1000)
}

const loadDetail = async (options = {}) => {
  const { preserveTab = false } = options
  if (!props.visible) {
    return
  }
  if (!preserveTab) {
    detailActiveTab.value = 'overview'
  }
  updateDetailWidth()
  if (!props.vmId) {
    currentVM.value = props.fallbackRecord || null
    return
  }
  detailLoading.value = true
  try {
    const res = await getVirtualMachine(props.vmId)
    currentVM.value = res
    await loadHardwareResources()
  } catch (error) {
    currentVM.value = props.fallbackRecord || null
    Message.error('获取虚拟机详情失败：' + (error.message || '未知错误'))
  } finally {
    detailLoading.value = false
  }
}

const loadHardwareResources = async () => {
  const vm = currentVM.value
  if (!vm || !vm.server || !vm.node) {
    storages.value = []
    networks.value = []
    isoStorages.value = []
    return
  }
  await Promise.all([fetchStorages(vm), fetchNetworks(vm)])
  isoStorages.value = storages.value.filter(item => item.content?.includes('iso') || item.type === 'dir' || item.type === 'nfs')
}

const fetchStorages = async (vm) => {
  storagesLoading.value = true
  try {
    const res = await getNodeStorage(vm.server, vm.node)
    storages.value = Array.isArray(res) ? res : []
  } catch (error) {
    storages.value = []
    Message.error('获取存储列表失败：' + (error.message || '未知错误'))
  } finally {
    storagesLoading.value = false
  }
}

const fetchNetworks = async (vm) => {
  networksLoading.value = true
  try {
    const res = await getNodeNetwork(vm.server, vm.node)
    networks.value = Array.isArray(res) ? res : []
  } catch (error) {
    networks.value = []
    Message.error('获取网络接口失败：' + (error.message || '未知错误'))
  } finally {
    networksLoading.value = false
  }
}

const getConfig = () => currentVM.value?.pve_config || {}

const resetEditForm = () => {
  Object.keys(editForm).forEach((key) => {
    delete editForm[key]
  })
}

const openEditDialog = (type) => {
  if (!currentVM.value) {
    return
  }
  const config = getConfig()
  resetEditForm()
  editState.type = type
  editState.submitting = false
  switch (type) {
    case 'cpu':
      editState.title = '编辑处理器'
      Object.assign(editForm, {
        sockets: Number(config.sockets || 1),
        cores: Number(config.cores || (currentVM.value.cpu_cores || 1)),
        cpu: config.cpu || 'x86-64-v2-AES',
        numa: config.numa === 1 || config.numa === '1' || config.numa === true
      })
      break
    case 'memory':
      editState.title = '编辑内存'
      Object.assign(editForm, {
        memory: Number(config.memory || currentVM.value.memory_mb || 512)
      })
      break
    case 'disk':
      editState.title = '编辑磁盘 (scsi0)'
      Object.assign(editForm, {
        scsi0: config.scsi0 || ''
      })
      break
    case 'network':
      editState.title = '编辑网络 (net0)'
      Object.assign(editForm, {
        net0: config.net0 || ''
      })
      break
    default:
      editState.title = '编辑硬件'
      break
  }
  editState.visible = true
  nextTick(() => {
    editFormRef.value?.clearValidate()
  })
}

const editFormRules = computed(() => {
  switch (editState.type) {
    case 'cpu':
      return {
        sockets: [{ required: true, message: '请输入Sockets', type: 'number' }],
        cores: [{ required: true, message: '请输入核心数', type: 'number' }],
        cpu: [{ required: true, message: '请选择CPU类型' }]
      }
    case 'memory':
      return {
        memory: [{ required: true, message: '请输入内存大小', type: 'number' }]
      }
    case 'disk':
      return {
        scsi0: [{ required: true, message: '请输入磁盘配置' }]
      }
    case 'network':
      return {
        net0: [{ required: true, message: '请输入网络配置' }]
      }
    default:
      return {}
  }
})

const buildParams = () => {
  switch (editState.type) {
    case 'cpu':
      return {
        sockets: Number(editForm.sockets),
        cores: Number(editForm.cores),
        cpu: editForm.cpu,
        numa: editForm.numa ? 1 : 0
      }
    case 'memory':
      return {
        memory: Number(editForm.memory)
      }
    case 'disk':
      return {
        scsi0: editForm.scsi0
      }
    case 'network':
      return {
        net0: editForm.net0
      }
    default:
      return {}
  }
}

const handleEditCancel = () => {
  editState.visible = false
}

const handleEditSubmit = async () => {
  if (!props.vmId) {
    Message.warning('缺少虚拟机ID，无法更新硬件配置')
    return
  }
  if (editFormRef.value) {
    try {
      await editFormRef.value.validate()
    } catch (error) {
      return
    }
  }
  const params = buildParams()
  if (!Object.keys(params).length) {
    Message.warning('暂无可更新的参数')
    return
  }
  editState.submitting = true
  try {
    await updateVirtualMachineHardware(props.vmId, { params })
    Message.success('硬件配置更新已提交')
    editState.visible = false
    await loadDetail({ preserveTab: true })
    detailActiveTab.value = 'hardware'
  } catch (error) {
    Message.error('更新失败：' + (error.message || '未知错误'))
  } finally {
    editState.submitting = false
  }
}

const getNextDeviceKey = (prefix, startIndex = 0) => {
  const config = getConfig()
  let index = startIndex
  while (config.hasOwnProperty(`${prefix}${index}`)) {
    index += 1
  }
  return `${prefix}${index}`
}

const openAddHardwareDialog = (type) => {
  if (!currentVM.value) return
  addState.type = type
  addState.title = hardwareAddOptions.find(item => item.type === type)?.label || '添加硬件'
  addState.submitting = false
  Object.keys(addForm).forEach(key => delete addForm[key])
  switch (type) {
    case 'disk':
      addForm.storage = storages.value[0]?.storage || ''
      addForm.size = 10
      addForm.iothread = true
      break
    case 'cdrom':
      addForm.isoStorage = isoStorages.value[0]?.storage || ''
      addForm.iso = ''
      if (addForm.isoStorage) {
        handleISOStorageChange(addForm.isoStorage)
      }
      break
    case 'network':
      addForm.model = 'virtio'
      addForm.bridge = bridgeOptions.value[0] || 'vmbr0'
      addForm.macaddr = ''
      addForm.firewall = true
      break
    case 'efi':
      addForm.storage = storages.value[0]?.storage || ''
      addForm.efitype = '4m'
      addForm.pre_enrolled = true
      break
    case 'tpm':
      addForm.storage = storages.value[0]?.storage || ''
      addForm.version = 'v2.0'
      addForm.model = 'tpm-crb'
      break
    case 'usb':
      addForm.host = ''
      addForm.usb3 = true
      break
    case 'pci':
      addForm.host = ''
      addForm.pcie = true
      break
    case 'serial':
      addForm.mode = 'socket'
      addForm.path = ''
      break
    case 'cloudinit':
      addForm.storage = storages.value[0]?.storage || ''
      addForm.ciuser = 'root'
      addForm.cipassword = ''
      addForm.ipconfig0 = 'ip=dhcp'
      break
    case 'audio':
      addForm.device = 'ich9-intel-hda'
      addForm.driver = 'spice'
      break
    case 'rng':
      addForm.source = '/dev/urandom'
      break
    case 'virtiofs':
      addForm.tag = 'share'
      addForm.path = '/mnt/share'
      break
  }
  addState.visible = true
  nextTick(() => {
    addFormRef.value?.clearValidate()
  })
}

const macPattern = /^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/

const addFormRules = computed(() => {
  switch (addState.type) {
    case 'disk':
      return {
        storage: [{ required: true, message: '请选择存储' }],
        size: [{ required: true, message: '请输入容量', type: 'number' }]
      }
    case 'cdrom':
      return {
        isoStorage: [{ required: true, message: '请选择ISO存储' }],
        iso: [{ required: true, message: '请选择ISO镜像' }]
      }
    case 'network':
      return {
        bridge: [{ required: true, message: '请选择桥接' }],
        macaddr: [{
          validator: (value, callback) => {
            if (!value) return callback()
            if (macPattern.test(value)) return callback()
            return callback('MAC地址格式不正确')
          }
        }]
      }
    case 'efi':
      return { storage: [{ required: true, message: '请选择存储' }] }
    case 'tpm':
      return { storage: [{ required: true, message: '请选择存储' }] }
    case 'usb':
      return { host: [{ required: true, message: '请输入设备ID (Vendor:Product)' }] }
    case 'pci':
      return { host: [{ required: true, message: '请输入PCI地址' }] }
    case 'cloudinit':
      return {
        storage: [{ required: true, message: '请选择存储' }],
        ciuser: [{ required: true, message: '请输入默认用户' }]
      }
    case 'virtiofs':
      return {
        tag: [{ required: true, message: '请输入Mount Tag' }],
        path: [{ required: true, message: '请输入路径' }]
      }
    default:
      return {}
  }
})

const handleISOStorageChange = async (storage) => {
  if (!storage || !currentVM.value) {
    isoList.value = []
    addForm.iso = ''
    return
  }
  isoLoading.value = true
  try {
    const res = await getStorageISO(currentVM.value.server, currentVM.value.node, storage)
    isoList.value = Array.isArray(res) ? res : []
    addForm.iso = isoList.value[0]?.volid || ''
  } catch (error) {
    isoList.value = []
    addForm.iso = ''
    Message.error('获取ISO列表失败：' + (error.message || '未知错误'))
  } finally {
    isoLoading.value = false
  }
}

const buildAddParams = () => {
  switch (addState.type) {
    case 'disk': {
      const storageInfo = storages.value.find(s => s.storage === addForm.storage)
      const storageType = storageInfo?.type || ''
      const size = Number(addForm.size)
      const base = ['rbd', 'lvm', 'lvmthin'].includes(storageType)
        ? `${addForm.storage}:${size}`
        : `${addForm.storage}:${size}G`
      const value = addForm.iothread ? `${base},iothread=on` : base
      const key = getNextDeviceKey('scsi')
      return { key, value }
    }
    case 'cdrom': {
      const key = getNextDeviceKey('ide', 2)
      const value = `${addForm.iso},media=cdrom`
      return { key, value }
    }
    case 'network': {
      const key = getNextDeviceKey('net')
      const parts = [addForm.model || 'virtio']
      if (addForm.bridge) parts.push(`bridge=${addForm.bridge}`)
      if (addForm.macaddr) parts.push(`macaddr=${addForm.macaddr}`)
      parts.push(`firewall=${addForm.firewall ? 1 : 0}`)
      return { key, value: parts.join(',') }
    }
    case 'efi': {
      if (getConfig().efidisk0) throw new Error('已存在EFI磁盘，请先移除')
      const value = `${addForm.storage}:1,efitype=${addForm.efitype || '4m'},pre-enrolled-keys=${addForm.pre_enrolled ? 1 : 0}`
      return { key: 'efidisk0', value }
    }
    case 'tpm': {
      if (getConfig().tpmstate0) throw new Error('已存在TPM设备，请先移除')
      const value = `${addForm.storage}:4,version=${addForm.version || 'v2.0'},model=${addForm.model || 'tpm-crb'}`
      return { key: 'tpmstate0', value }
    }
    case 'usb': {
      const key = getNextDeviceKey('usb')
      const value = `${addForm.host}${addForm.usb3 ? ',usb3=1' : ''}`
      return { key, value }
    }
    case 'pci': {
      const key = getNextDeviceKey('hostpci')
      const value = `${addForm.host}${addForm.pcie ? ',pcie=1' : ''}`
      return { key, value }
    }
    case 'serial': {
      const key = getNextDeviceKey('serial')
      const value = addForm.path ? `${addForm.mode || 'socket'},path=${addForm.path}` : (addForm.mode || 'socket')
      return { key, value }
    }
    case 'cloudinit': {
      const value = `${addForm.storage}:cloudinit`
      const params = {
        ide2: value,
        ciuser: addForm.ciuser || 'root'
      }
      if (addForm.cipassword) params.cipassword = addForm.cipassword
      if (addForm.ipconfig0) params.ipconfig0 = addForm.ipconfig0
      return { params }
    }
    case 'audio': {
      if (getConfig().audio0) throw new Error('已存在音频设备，请先移除')
      const value = `device=${addForm.device || 'ich9-intel-hda'},driver=${addForm.driver || 'spice'}`
      return { key: 'audio0', value }
    }
    case 'rng': {
      if (getConfig().rng0) throw new Error('已存在RNG设备，请先移除')
      const value = `source=${addForm.source || '/dev/urandom'}`
      return { key: 'rng0', value }
    }
    case 'virtiofs': {
      const key = getNextDeviceKey('virtiofs')
      const value = `mount_tag=${addForm.tag},path=${addForm.path}`
      return { key, value }
    }
    default:
      return { key: '', value: '' }
  }
}

const handleAddCancel = () => {
  addState.visible = false
}

const handleAddSubmit = async () => {
  if (!props.vmId) return
  if (addFormRef.value) {
    try {
      await addFormRef.value.validate()
    } catch (error) {
      return
    }
  }
  let payload
  try {
    const result = buildAddParams()
    if (result.params) {
      payload = result.params
    } else if (result.key) {
      payload = { [result.key]: result.value }
    } else {
      Message.warning('无可提交的参数')
      return
    }
  } catch (error) {
    Message.error(error.message || '构建参数失败')
    return
  }
  addState.submitting = true
  try {
    await updateVirtualMachineHardware(props.vmId, { params: payload })
    Message.success(`${addState.title} 创建任务已提交`)
    addState.visible = false
    await loadDetail({ preserveTab: true })
    detailActiveTab.value = 'hardware'
  } catch (error) {
    Message.error('添加硬件失败：' + (error.message || '未知错误'))
  } finally {
    addState.submitting = false
  }
}

watch(
  () => props.visible,
  (val) => {
    if (val) {
       loadDetail()
     } else {
       currentVM.value = null
       editState.visible = false
       addState.visible = false
       cleanupConsole()
     }
  }
)

watch(
  () => props.vmId,
   (val, oldVal) => {
     if (props.visible && val !== oldVal) {
       loadDetail()
      if (detailActiveTab.value === 'console') {
        initConsole()
      }
     }
   }
 )

watch(
  () => detailActiveTab.value,
  async (tab) => {
    if (tab === 'console') {
      // 等待 DOM 更新后再初始化
      await nextTick()
      // 再延迟一点确保容器元素已完全渲染
      setTimeout(() => {
        initConsole()
      }, 50)
    } else {
      cleanupConsole()
    }
  }
)

 onMounted(() => {
   updateDetailWidth()
   window.addEventListener('resize', updateDetailWidth)
   if (props.visible) {
     loadDetail()
   }
 })

 onBeforeUnmount(() => {
   cleanupConsole()
   window.removeEventListener('resize', updateDetailWidth)
   window.removeEventListener('resize', updateDetailWidth)
 })
</script>

<style scoped>
.vm-detail {
  width: 100%;
  overflow: hidden;
}

.vm-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.vm-detail-name {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-1);
}

.vm-detail-sub {
  color: var(--color-text-3);
  margin-top: 4px;
}

.console-placeholder {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  padding: 24px;
  background: var(--color-fill-2);
  border-radius: 8px;
}

.config-pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: var(--font-family-code);
  font-size: 12px;
  line-height: 1.4;
}

.hardware-value {
  white-space: pre-wrap;
  word-break: break-all;
}

.hardware-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.edit-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.novnc-wrapper {
  width: 100%;
  min-height: 420px;
  border: 1px solid var(--color-border-2);
  border-radius: 8px;
  background: #000;
  position: relative;
  overflow: hidden;
}

.novnc-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-3);
  text-align: center;
}

.novnc-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
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
  width: 100%;
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
  width: 100% !important;
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
  max-width: 100% !important;
  max-height: 100% !important;
  /* 确保 canvas 在容器中水平和垂直居中 */
  position: relative !important;
}

.pve-console-iframe {
  width: 100%;
  height: 480px;
  border: 0;
  background: #000;
}

/* 确保 a-card 内容区域也居中 */
:deep(.arco-card-body) {
  text-align: center;
}

/* 确保控制台卡片内的内容居中 */
:deep(.arco-tabs-content) {
  text-align: left;
}

:deep(.arco-tabs-content .arco-card-body) {
  text-align: center;
}
</style>

