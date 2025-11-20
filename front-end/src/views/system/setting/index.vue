<template>
  <div class="system-setting">
    <a-card>
      <template #title>
        <a-typography-title :heading="4">系统设置</a-typography-title>
      </template>

      <!-- 工具栏 -->
      <div class="toolbar">
        <a-space>
          <a-input-search
            v-model="searchText"
            placeholder="搜索配置键或描述"
            style="width: 300px"
            @search="handleSearch"
            @clear="handleSearch"
            allow-clear
          />
          <a-select
            v-model="selectedCategory"
            placeholder="选择分类"
            style="width: 150px"
            allow-clear
            @change="handleCategoryChange"
          >
            <a-option value="ai">AI 配置</a-option>
            <a-option value="email">邮件配置</a-option>
            <a-option value="storage">存储配置</a-option>
            <a-option value="general">通用配置</a-option>
          </a-select>
          <a-button type="primary" @click="handleCreate">
            <template #icon>
              <icon-plus />
            </template>
            新增配置
          </a-button>
          <a-button @click="handleBulkUpdate" :disabled="!hasChanges">
            <template #icon>
              <icon-save />
            </template>
            保存所有更改
          </a-button>
        </a-space>
      </div>

      <!-- 按分类展示的设置 -->
      <div class="settings-container">
        <a-tabs v-model:active-key="activeTab" type="card-gutter">
          <a-tab-pane
            v-for="category in categories"
            :key="category.key"
            :title="category.label"
          >
            <a-table
              :columns="columns"
              :data="getCategoryData(category.key)"
              :loading="loading"
              :pagination="false"
              :bordered="false"
              :hoverable="true"
              style="margin-top: 16px"
            >
              <template #value="{ record }">
                <a-input
                  v-if="!record.is_encrypted || showEncrypted[record.id]"
                  v-model="record.value"
                  :placeholder="record.description"
                  @change="handleValueChange(record)"
                />
                <a-input-password
                  v-else
                  v-model="record.value"
                  :placeholder="record.description"
                  @change="handleValueChange(record)"
                />
              </template>

              <template #is_encrypted="{ record }">
                <a-tag :color="record.is_encrypted ? 'orange' : 'blue'">
                  {{ record.is_encrypted ? '加密' : '明文' }}
                </a-tag>
              </template>

              <template #is_public="{ record }">
                <a-tag :color="record.is_public ? 'green' : 'red'">
                  {{ record.is_public ? '公开' : '私有' }}
                </a-tag>
              </template>

              <template #actions="{ record }">
                <a-button type="text" size="small" @click="handleEdit(record)">编辑</a-button>
                <a-button type="text" size="small" status="danger" @click="handleDelete(record)">删除</a-button>
              </template>
            </a-table>
          </a-tab-pane>
        </a-tabs>
      </div>
    </a-card>

    <!-- 表单对话框 -->
    <a-modal
      v-model:visible="formVisible"
      :title="formTitle"
      @before-ok="handleSubmit"
      @cancel="handleCancel"
      :width="600"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        layout="vertical"
      >
        <a-form-item field="key" label="配置键" v-if="!isEdit">
          <a-input
            v-model="formData.key"
            placeholder="请输入配置键，如：ai_openai_api_key"
            :disabled="isEdit"
          />
        </a-form-item>

        <a-form-item field="value" label="配置值">
          <a-textarea
            v-model="formData.value"
            :placeholder="formData.description || '请输入配置值'"
            :auto-size="{ minRows: 3, maxRows: 6 }"
          />
        </a-form-item>

        <a-form-item field="description" label="描述">
          <a-input
            v-model="formData.description"
            placeholder="请输入配置描述"
          />
        </a-form-item>

        <a-form-item field="category" label="分类">
          <a-select v-model="formData.category" placeholder="请选择分类">
            <a-option value="ai">AI 配置</a-option>
            <a-option value="email">邮件配置</a-option>
            <a-option value="storage">存储配置</a-option>
            <a-option value="general">通用配置</a-option>
          </a-select>
        </a-form-item>

        <a-form-item field="is_encrypted" label="是否加密">
          <a-switch v-model="formData.is_encrypted" />
          <template #extra>
            <span style="color: #86909c; font-size: 12px">敏感信息建议开启加密</span>
          </template>
        </a-form-item>

        <a-form-item field="is_public" label="是否公开">
          <a-switch v-model="formData.is_public" />
          <template #extra>
            <span style="color: #86909c; font-size: 12px">公开配置可在前端显示</span>
          </template>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { IconPlus, IconSave } from '@arco-design/web-vue/es/icon'
import {
  getSystemSettings,
  getSystemSetting,
  createSystemSetting,
  updateSystemSetting,
  deleteSystemSetting,
  bulkUpdateSystemSettings
} from '@/api/system-setting'

const columns = [
  { title: '配置键', dataIndex: 'key', width: 200 },
  { title: '配置值', dataIndex: 'value', slotName: 'value' },
  { title: '描述', dataIndex: 'description', width: 200 },
  { title: '加密', dataIndex: 'is_encrypted', slotName: 'is_encrypted', width: 80 },
  { title: '公开', dataIndex: 'is_public', slotName: 'is_public', width: 80 },
  { title: '操作', slotName: 'actions', width: 150, fixed: 'right' }
]

const categories = [
  { key: 'all', label: '全部' },
  { key: 'ai', label: 'AI 配置' },
  { key: 'email', label: '邮件配置' },
  { key: 'storage', label: '存储配置' },
  { key: 'general', label: '通用配置' }
]

const loading = ref(false)
const searchText = ref('')
const selectedCategory = ref('')
const activeTab = ref('all')
const tableData = ref([])
const originalData = ref([])
const formVisible = ref(false)
const formTitle = ref('新增配置')
const isEdit = ref(false)
const showEncrypted = ref({})
const changedSettings = ref(new Set())

const formData = reactive({
  key: '',
  value: '',
  description: '',
  category: 'general',
  is_encrypted: false,
  is_public: false,
  remark: ''
})

const formRules = {
  key: [
    { required: true, message: '请输入配置键' },
    { match: /^[a-z_][a-z0-9_]*$/, message: '配置键只能包含小写字母、数字和下划线，且不能以数字开头' }
  ],
  value: [
    { required: true, message: '请输入配置值' }
  ],
  category: [
    { required: true, message: '请选择分类' }
  ]
}

const formRef = ref(null)

const hasChanges = computed(() => {
  return changedSettings.value.size > 0
})

const getCategoryData = (category) => {
  let data = tableData.value

  if (category !== 'all') {
    data = data.filter(item => item.category === category)
  }

  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    data = data.filter(item =>
      item.key.toLowerCase().includes(search) ||
      (item.description && item.description.toLowerCase().includes(search))
    )
  }

  return data
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {}
    if (selectedCategory.value) {
      params.category = selectedCategory.value
    }
    if (searchText.value) {
      params.search = searchText.value
    }
    const res = await getSystemSettings(params)
    // request 封装已经返回的是 response.data，这里直接从 res 里取分页数据
    if (Array.isArray(res)) {
      tableData.value = res
    } else if (Array.isArray(res.results)) {
      tableData.value = res.results
    } else {
      tableData.value = []
    }
    originalData.value = JSON.parse(JSON.stringify(tableData.value))
    changedSettings.value.clear()
  } catch (error) {
    Message.error('获取系统设置失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  fetchData()
}

const handleCategoryChange = () => {
  fetchData()
}

const handleCreate = () => {
  isEdit.value = false
  formTitle.value = '新增配置'
  Object.assign(formData, {
    key: '',
    value: '',
    description: '',
    category: 'general',
    is_encrypted: false,
    is_public: false,
    remark: ''
  })
  formVisible.value = true
}

const handleEdit = (record) => {
  isEdit.value = true
  formTitle.value = '编辑配置'
  Object.assign(formData, {
    key: record.key,
    value: record.value,
    description: record.description,
    category: record.category,
    is_encrypted: record.is_encrypted,
    is_public: record.is_public,
    remark: record.remark || ''
  })
  formVisible.value = true
}

const handleDelete = (record) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除配置 "${record.key}" 吗？`,
    onOk: async () => {
      try {
        await deleteSystemSetting(record.id)
        Message.success('删除成功')
        fetchData()
      } catch (error) {
        Message.error('删除失败：' + (error.message || '未知错误'))
      }
    }
  })
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    if (isEdit.value) {
      // 找到对应的记录
      const record = tableData.value.find(item => item.key === formData.key)
      if (record) {
        await updateSystemSetting(record.id, {
          value: formData.value,
          description: formData.description,
          category: formData.category,
          is_encrypted: formData.is_encrypted,
          is_public: formData.is_public,
          remark: formData.remark
        })
        Message.success('更新成功')
      }
    } else {
      await createSystemSetting(formData)
      Message.success('创建成功')
    }
    
    formVisible.value = false
    fetchData()
  } catch (error) {
    if (error.errors) {
      // 表单验证错误
      return false
    }
    Message.error((isEdit.value ? '更新' : '创建') + '失败：' + (error.message || '未知错误'))
    return false
  }
}

const handleCancel = () => {
  formVisible.value = false
}

const handleValueChange = (record) => {
  changedSettings.value.add(record.id)
}

const handleBulkUpdate = async () => {
  if (changedSettings.value.size === 0) {
    Message.warning('没有需要保存的更改')
    return
  }

  const settingsToUpdate = tableData.value
    .filter(item => changedSettings.value.has(item.id))
    .map(item => ({
      key: item.key,
      value: item.value
    }))

  try {
    await bulkUpdateSystemSettings({ settings: settingsToUpdate })
    Message.success(`成功保存 ${settingsToUpdate.length} 个配置`)
    changedSettings.value.clear()
    fetchData()
  } catch (error) {
    Message.error('批量更新失败：' + (error.message || '未知错误'))
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.system-setting {
  padding: 20px;
}

.toolbar {
  margin-bottom: 16px;
}

.settings-container {
  margin-top: 16px;
}
</style>

