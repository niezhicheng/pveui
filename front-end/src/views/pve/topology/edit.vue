<template>
  <div class="pve-topology-edit">
    <a-page-header
      title="拓扑编辑"
      :subtitle="pageSubtitle"
      :back-icon="true"
      @back="handleBack"
    >
      <template #extra>
        <a-space>
          <a-button @click="handleFitView">
            <icon-fullscreen />
            自适应
          </a-button>
          <a-button @click="handleResetCanvas">
            <icon-refresh />
            清空画布
          </a-button>
          <a-button @click="handleSnapshot">
            <icon-download />
            导出图片
          </a-button>
          <a-button type="primary" :loading="saving" @click="handleSaveTopology">
            <icon-save />
            保存拓扑
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-row :gutter="16" class="edit-body">
      <a-col :span="6">
        <a-card title="基础信息" :loading="detailLoading" class="info-card">
          <a-form :model="topologyForm" layout="vertical">
            <a-form-item field="name" label="名称" required>
              <a-input v-model="topologyForm.name" placeholder="例如：生产集群网络拓扑" />
            </a-form-item>
            <a-form-item field="description" label="描述">
              <a-textarea
                v-model="topologyForm.description"
                placeholder="补充拓扑用途、包含资源等信息"
                :auto-size="{ minRows: 2, maxRows: 4 }"
              />
            </a-form-item>
            <a-form-item field="is_active" label="状态">
              <a-switch v-model="topologyForm.is_active" checked-text="启用" unchecked-text="禁用" />
            </a-form-item>
            <a-descriptions :column="1" size="small" bordered>
              <a-descriptions-item label="节点数">{{ graphStats.nodes }}</a-descriptions-item>
              <a-descriptions-item label="连线数">{{ graphStats.edges }}</a-descriptions-item>
            </a-descriptions>
          </a-form>
        </a-card>

        <a-card title="元素面板" class="palette-card">
          <a-space wrap>
            <a-button
              v-for="item in palette"
              :key="item.type"
              size="small"
              type="secondary"
              @click="() => addNode(item)"
            >
              <span class="palette-dot" :style="{ background: item.color }" />
              {{ item.label }}
            </a-button>
          </a-space>
          <div class="palette-hint">点击按钮即可向画布添加节点，使用拖拽连线完成拓扑关系。</div>
        </a-card>
      </a-col>

      <a-col :span="18">
        <a-card class="canvas-card" :loading="canvasLoading">
          <div ref="canvasRef" class="logicflow-canvas" />
        </a-card>
      </a-col>
    </a-row>

    <a-drawer
      v-model:visible="nodeDrawerVisible"
      title="编辑节点"
      width="360px"
      unmount-on-close
    >
      <a-form :model="nodeForm" layout="vertical">
        <a-form-item field="title" label="名称" required>
          <a-input v-model="nodeForm.title" placeholder="节点名称，如：Node01 或 VM-001" />
        </a-form-item>
        <a-form-item field="interface" label="网口 / 接口名称">
          <a-input v-model="nodeForm.interface" placeholder="例如：eth0、vmbr0、tap100i0" />
        </a-form-item>
        <a-form-item field="network" label="网段 / VLAN">
          <a-input v-model="nodeForm.network" placeholder="例如：192.168.10.0/24 或 VLAN 20" />
        </a-form-item>
        <a-form-item field="description" label="备注">
          <a-textarea
            v-model="nodeForm.description"
            placeholder="可记录用途、带宽等补充信息"
            :auto-size="{ minRows: 2, maxRows: 4 }"
          />
        </a-form-item>
      </a-form>
      <template #footer>
        <a-space>
          <a-button @click="nodeDrawerVisible = false">取消</a-button>
          <a-button type="primary" @click="handleSaveNode">保存</a-button>
        </a-space>
      </template>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import {
  IconSave,
  IconRefresh,
  IconFullscreen,
  IconDownload
} from '@arco-design/web-vue/es/icon'
import LogicFlow from '@logicflow/core'
import { MiniMap, Snapshot, SelectionSelect } from '@logicflow/extension'
import '@logicflow/core/es/index.css'
import '@logicflow/extension/es/index.css'
import {
  getNetworkTopology,
  createNetworkTopology,
  updateNetworkTopology
} from '@/api/pve'

const route = useRoute()
const router = useRouter()
const topologyId = computed(() => route.params.id)

const canvasRef = ref(null)
const logicflow = ref(null)
const canvasLoading = ref(false)
const detailLoading = ref(false)
const saving = ref(false)
const nodeDrawerVisible = ref(false)
const currentTopology = ref(null)
const pendingGraphData = ref(null)
const graphStats = reactive({ nodes: 0, edges: 0 })

const topologyForm = reactive({
  name: '',
  description: '',
  is_active: true
})

const nodeForm = reactive({
  id: '',
  title: '',
  interface: '',
  network: '',
  description: '',
  borderColor: '#165dff'
})

const palette = [
  { type: 'pve-node', label: 'PVE 节点', color: '#165dff' },
  { type: 'vm-node', label: '虚拟机', color: '#00b42a' },
  { type: 'network-node', label: '网络设备', color: '#ff7d00' },
  { type: 'storage-node', label: '存储', color: '#722ed1' }
]

const defaultGraphData = { nodes: [], edges: [] }

const pageSubtitle = computed(() => {
  if (topologyId.value) {
    return currentTopology.value?.name ? `编辑：${currentTopology.value.name}` : '编辑拓扑'
  }
  return '新建拓扑'
})

const handleBack = () => {
  router.push('/pve/topology/index')
}

const initLogicFlow = () => {
  if (!canvasRef.value) return
  logicflow.value = new LogicFlow({
    container: canvasRef.value,
    grid: true,
    plugins: [MiniMap, Snapshot, SelectionSelect],
    background: { color: '#fafafa' }
  })
  logicflow.value.setDefaultEdgeType('polyline')
  logicflow.value.render(defaultGraphData)
  logicflow.value.on('node:add', () => updateGraphStats())
  logicflow.value.on('edge:add', () => updateGraphStats())
  logicflow.value.on('edge:delete', () => updateGraphStats())
  logicflow.value.on('node:delete', ({ data }) => {
    if (data?.id === nodeForm.id) {
      nodeDrawerVisible.value = false
    }
    updateGraphStats()
  })
  logicflow.value.on('node:click', ({ data }) => {
    if (data) openNodeDrawer(data)
  })
  if (pendingGraphData.value) {
    renderGraph(pendingGraphData.value)
  }
}

const formatNodeText = (title, interfaceName, network) => {
  const lines = []
  if (title) lines.push(title)
  if (interfaceName) lines.push(`[${interfaceName}]`)
  if (network) lines.push(network)
  return lines.join('\n') || '未命名节点'
}

const applyNodeVisual = (nodeId, color = '#165dff') => {
  const lf = logicflow.value
  if (!lf) return
  const nodeModel = lf.graphModel?.getNodeModelById(nodeId)
  if (nodeModel) {
    nodeModel.updateStyles({
      stroke: color || '#165dff',
      fill: '#fff',
      borderRadius: 6
    })
  }
}

const openNodeDrawer = (data) => {
  const props = data.properties || {}
  nodeForm.id = data.id
  nodeForm.title = props.title || data.text?.value?.split('\n')[0] || ''
  nodeForm.interface = props.interface || ''
  nodeForm.network = props.network || ''
  nodeForm.description = props.description || ''
  nodeForm.borderColor = props.borderColor || props.stroke || '#165dff'
  nodeDrawerVisible.value = true
}

const renderGraph = (data) => {
  pendingGraphData.value = data || defaultGraphData
  if (!logicflow.value) return
  canvasLoading.value = true
  const graphData = pendingGraphData.value
  logicflow.value.render(graphData)
  updateGraphStats(graphData)
  nextTick(() => {
    (graphData?.nodes || []).forEach(node => {
      const props = node.properties || {}
      if (props.title || props.interface || props.network) {
        const text = formatNodeText(
          props.title || node.text,
          props.interface,
          props.network
        )
        logicflow.value.updateText(node.id, text)
      }
      applyNodeVisual(node.id, props.borderColor || '#165dff')
    })
    canvasLoading.value = false
  })
}

const updateGraphStats = (graphData) => {
  const data = graphData || (logicflow.value ? logicflow.value.getGraphData() : defaultGraphData)
  graphStats.nodes = Array.isArray(data?.nodes) ? data.nodes.length : 0
  graphStats.edges = Array.isArray(data?.edges) ? data.edges.length : 0
}

const addNode = (paletteItem) => {
  if (!logicflow.value) return
  const rect = canvasRef.value.getBoundingClientRect()
  const x = rect.width / 2 + (Math.random() * 80 - 40)
  const y = rect.height / 2 + (Math.random() * 80 - 40)
  const node = logicflow.value.addNode({
    type: 'rect',
    x,
    y,
    text: paletteItem.label,
    width: 120,
    height: 40,
    properties: {
      title: paletteItem.label,
      category: paletteItem.type,
      borderColor: paletteItem.color,
      interface: '',
      network: '',
      description: ''
    },
    style: {
      stroke: paletteItem.color,
      fill: '#fff',
      borderRadius: 6
    }
  })
  if (node?.id) {
    const text = formatNodeText(paletteItem.label, '', '')
    logicflow.value.updateText(node.id, text)
    applyNodeVisual(node.id, paletteItem.color)
  }
}

const handleSaveNode = () => {
  if (!logicflow.value || !nodeForm.id) {
    Message.warning('请先选择节点')
    return
  }
  const lf = logicflow.value
  const nodeModel = lf.graphModel?.getNodeModelById(nodeForm.id)
  const category = nodeModel?.properties?.category || 'custom'
  const text = formatNodeText(nodeForm.title, nodeForm.interface, nodeForm.network)
  lf.updateText(nodeForm.id, text)
  lf.setProperties(nodeForm.id, {
    title: nodeForm.title,
    interface: nodeForm.interface,
    network: nodeForm.network,
    description: nodeForm.description,
    borderColor: nodeForm.borderColor,
    category
  })
  applyNodeVisual(nodeForm.id, nodeForm.borderColor)
  nodeDrawerVisible.value = false
  Message.success('节点信息已更新')
}

const handleResetCanvas = () => {
  if (!logicflow.value) return
  logicflow.value.clearData()
  logicflow.value.render(defaultGraphData)
  updateGraphStats(defaultGraphData)
}

const handleFitView = () => {
  if (!logicflow.value) return
  logicflow.value.view.fitView()
}

const handleSnapshot = async () => {
  if (!logicflow.value) return
  try {
    const snapshot = await logicflow.value.getSnapshot()
    const link = document.createElement('a')
    link.href = snapshot
    link.download = `${topologyForm.name || 'topology'}.png`
    link.click()
  } catch (error) {
    Message.error('导出图片失败')
  }
}

const collectGraphData = () => {
  if (!logicflow.value) return defaultGraphData
  return logicflow.value.getGraphData()
}

const handleSaveTopology = async () => {
  if (!topologyForm.name.trim()) {
    Message.warning('拓扑名称不能为空')
    return
  }
  const payload = {
    name: topologyForm.name.trim(),
    description: topologyForm.description || '',
    is_active: topologyForm.is_active,
    diagram_data: collectGraphData(),
    metadata: {
      ...(currentTopology.value?.metadata || {}),
      stats: {
        nodes: graphStats.nodes,
        edges: graphStats.edges,
        updated_at: new Date().toISOString()
      }
    }
  }
  saving.value = true
  try {
    if (topologyId.value) {
      const res = await updateNetworkTopology(topologyId.value, payload)
      currentTopology.value = res
      Message.success('拓扑已保存')
    } else {
      const res = await createNetworkTopology(payload)
      Message.success('拓扑创建成功')
      if (res?.id) {
        router.replace({ name: 'PVETopologyEdit', params: { id: res.id } })
      }
    }
  } catch (error) {
    Message.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const loadTopologyDetail = async () => {
  if (!topologyId.value) {
    currentTopology.value = null
    Object.assign(topologyForm, {
      name: '',
      description: '',
      is_active: true
    })
    renderGraph(defaultGraphData)
    return
  }
  detailLoading.value = true
  try {
    const detail = await getNetworkTopology(topologyId.value)
    currentTopology.value = detail
    Object.assign(topologyForm, {
      name: detail.name || '',
      description: detail.description || '',
      is_active: detail.is_active ?? true
    })
    renderGraph(detail.diagram_data || defaultGraphData)
  } catch (error) {
    Message.error('加载拓扑详情失败：' + (error.message || '未知错误'))
  } finally {
    detailLoading.value = false
  }
}

watch(
  () => topologyId.value,
  () => {
    loadTopologyDetail()
  }
)

onMounted(async () => {
  await nextTick()
  initLogicFlow()
  loadTopologyDetail()
})

onBeforeUnmount(() => {
  if (logicflow.value) {
    logicflow.value.destroy()
  }
})
</script>

<style scoped>
.pve-topology-edit {
  padding: 16px;
}

.edit-body {
  margin-top: 16px;
}

.logicflow-canvas {
  height: 640px;
  border: 1px dashed var(--color-border-2);
  border-radius: 8px;
  background: #fff;
}

.palette-card,
.info-card,
.canvas-card {
  margin-bottom: 16px;
}

.palette-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 4px;
}

.palette-hint {
  margin-top: 12px;
  font-size: 12px;
  color: var(--color-text-3);
}
</style>



