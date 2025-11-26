<template>
  <div class="vm-options-tab">
    <a-card :bordered="false">
      <template #title>
        <div class="card-title">
          <span>虚拟机选项</span>
          <a-space>
            <a-button size="small" @click="loadOptions" :loading="loading">刷新</a-button>
            <a-button type="primary" size="small" @click="handleSave" :loading="saving" :disabled="!vmId">
              保存
            </a-button>
          </a-space>
        </div>
      </template>
      <a-spin :loading="loading">
        <a-form :model="form" layout="vertical" class="options-form">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="名称">
                <a-input v-model="form.name" placeholder="虚拟机名称" allow-clear />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="描述">
                <a-input v-model="form.description" placeholder="描述信息" allow-clear />
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item label="开机自启动">
                <a-switch v-model="form.onboot" />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="QEMU Guest Agent">
                <a-switch v-model="form.agent" />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="防删除保护">
                <a-switch v-model="form.protection" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="启动顺序 (boot)">
                <a-input
                  v-model="form.boot"
                  placeholder="示例：order=scsi0;net0"
                  allow-clear
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="启动磁盘 (bootdisk)">
                <a-select
                  v-model="form.bootdisk"
                  placeholder="选择启动磁盘"
                  allow-clear
                  :options="bootDiskOptions"
                />
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="BIOS">
                <a-select v-model="form.bios" placeholder="请选择BIOS" allow-clear>
                  <a-option value="seabios">SeaBIOS</a-option>
                  <a-option value="ovmf">OVMF (UEFI)</a-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="USB Tablet">
                <a-switch v-model="form.tablet" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="KVM 加速">
                <a-switch v-model="form.kvm" />
              </a-form-item>
            </a-col>
          </a-row>
        </a-form>
      </a-spin>
    </a-card>
  </div>
</template>

<script setup>
import { reactive, ref, watch, computed, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getVMOptions, updateVMOptions } from '@/api/pve'

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

const emit = defineEmits(['refresh'])

const loading = ref(false)
const saving = ref(false)
const originalConfig = ref({})

const form = reactive({
  name: '',
  description: '',
  onboot: false,
  boot: '',
  bootdisk: '',
  bios: '',
  agent: false,
  protection: false,
  tablet: false,
  kvm: true
})

const parseBool = (val) => {
  if (val === null || val === undefined) return false
  if (typeof val === 'boolean') return val
  const str = String(val).toLowerCase()
  return ['1', 'true', 'yes', 'on', 'enabled'].includes(str)
}

const assignConfigToForm = (config = {}) => {
  originalConfig.value = { ...config }
  form.name = config.name || props.vm?.name || ''
  form.description = config.description || props.vm?.description || ''
  form.onboot = parseBool(config.onboot)
  form.boot = config.boot || ''
  form.bootdisk = config.bootdisk || ''
  form.bios = config.bios || ''
  form.agent = parseBool(config.agent)
  form.protection = parseBool(config.protection)
  form.tablet = parseBool(config.tablet ?? config.usb0)
  form.kvm = config.kvm === undefined ? true : parseBool(config.kvm)
}

const bootDiskOptions = computed(() => {
  const config = originalConfig.value || {}
  const keys = Object.keys(config || {})
  const diskKeys = keys.filter((key) => /^(scsi|sata|ide|virtio|efidisk)\d+$/i.test(key))
  return diskKeys.map((key) => ({
    label: key.toUpperCase(),
    value: key
  }))
})

const loadOptions = async () => {
  if (!props.vmId) {
    assignConfigToForm(props.vm?.pve_config || {})
    return
  }
  loading.value = true
  try {
    const res = await getVMOptions(props.vmId)
    const config = res?.config || props.vm?.pve_config || {}
    assignConfigToForm(config)
  } catch (error) {
    Message.error('获取选项失败：' + (error.message || '未知错误'))
    assignConfigToForm(props.vm?.pve_config || {})
  } finally {
    loading.value = false
  }
}

const buildParams = () => {
  const params = {}
  const orig = originalConfig.value || {}
  if (form.name !== (orig.name || props.vm?.name || '')) {
    params.name = form.name || ''
  }
  if ((form.description || '') !== (orig.description || props.vm?.description || '')) {
    params.description = form.description || ''
  }
  if ((form.boot || '') !== (orig.boot || '')) {
    params.boot = form.boot || ''
  }
  if ((form.bootdisk || '') !== (orig.bootdisk || '')) {
    params.bootdisk = form.bootdisk || ''
  }
  if ((form.bios || '') !== (orig.bios || '')) {
    params.bios = form.bios || ''
  }
  const boolFields = [
    ['onboot', 'onboot'],
    ['agent', 'agent'],
    ['protection', 'protection'],
    ['tablet', 'tablet'],
    ['kvm', 'kvm']
  ]
  boolFields.forEach(([field, key]) => {
    if (form[field] !== parseBool(orig[key])) {
      params[key] = form[field] ? 1 : 0
    }
  })
  return params
}

const handleSave = async () => {
  if (!props.vmId) {
    Message.warning('缺少虚拟机ID，无法保存')
    return
  }
  const params = buildParams()
  if (Object.keys(params).length === 0) {
    Message.info('没有需要保存的更改')
    return
  }
  saving.value = true
  try {
    await updateVMOptions(props.vmId, { params })
    Message.success('选项已更新')
    emit('refresh')
    loadOptions()
  } catch (error) {
    Message.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

watch(
  () => props.vmId,
  (val, oldVal) => {
    if (val && val !== oldVal) {
      loadOptions()
    }
  }
)

watch(
  () => props.vm?.pve_config,
  (config) => {
    if (!props.vmId && config) {
      assignConfigToForm(config)
    }
  },
  { deep: true }
)

onMounted(() => {
  loadOptions()
})
</script>

<style scoped>
.vm-options-tab {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.options-form {
  margin-top: 8px;
}

.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>

