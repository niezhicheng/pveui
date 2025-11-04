<template>
  <div class="${model_name}-page">
    <a-card>
      <template #title>
        <a-typography-title :heading="4">${ModelName} 管理</a-typography-title>
      </template>

      <div class="toolbar">
        <a-space>
          <a-input-search v-model="searchText" placeholder="搜索" style="width: 300px" @search="fetchData" allow-clear />
          <a-button type="primary" @click="handleCreate">新增</a-button>
        </a-space>
      </div>

      <a-table :columns="columns" :data="tableData" :loading="loading" :pagination="pagination" style="margin-top: 16px">
        <template #actions="{ record }">
          <a-button type="text" size="small" @click="handleEdit(record)">编辑</a-button>
          <a-button type="text" size="small" status="danger" @click="handleDelete(record)">删除</a-button>
        </template>
      </a-table>
    </a-card>

    <a-modal v-model:visible="formVisible" :title="formTitle" @before-ok="handleSubmit" @cancel="() => (formVisible=false)" :width="600">
      <a-form ref="formRef" :model="formData" layout="vertical">
        <!-- 简化：仅生成通用字段，具体按需二开 -->
        <a-form-item field="id" label="ID">
          <a-input v-model="formData.id" disabled />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { get${ModelName}List, get${ModelName}Detail, create${ModelName}, update${ModelName}, delete${ModelName} } from '@/api/${model_name}'

const columns = [
  { title: 'ID', dataIndex: 'id', width: 100 },
  { title: '操作', slotName: 'actions', width: 150, fixed: 'right' }
]

const searchText = ref('')
const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ current: 1, pageSize: 20, total: 0, showTotal: true, showPageSize: true })

const formVisible = ref(false)
const formTitle = ref('新增')
const formRef = ref()
const formData = reactive({ id: null })

const fetchData = async () => {
  loading.value = true
  try {
    const res = await get${ModelName}List({ page: pagination.current, page_size: pagination.pageSize, search: searchText.value || undefined })
    tableData.value = res.results || res.data || []
    pagination.total = res.count || res.total || 0
  } catch (e) {
    Message.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  formTitle.value = '新增'
  Object.assign(formData, { id: null })
  formVisible.value = true
}

const handleEdit = async (record) => {
  formTitle.value = '编辑'
  const res = await get${ModelName}Detail(record.id)
  Object.assign(formData, res)
  formVisible.value = true
}

const handleDelete = (record) => {
  Modal.confirm({
    title: '确认删除',
    onOk: async () => {
      await delete${ModelName}(record.id)
      Message.success('删除成功')
      fetchData()
    }
  })
}

const handleSubmit = async () => {
  try {
    if (formData.id) {
      await update${ModelName}(formData.id, formData)
      Message.success('更新成功')
    } else {
      await create${ModelName}(formData)
      Message.success('创建成功')
    }
    formVisible.value = false
    fetchData()
    return true
  } catch (e) {
    Message.error('提交失败')
    return false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.toolbar { margin-bottom: 16px; }
</style>

