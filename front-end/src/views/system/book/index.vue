<template>
  <div class="book-page">
    <a-card>
      <template #title>
        <a-typography-title :heading="4">Book 管理</a-typography-title>
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
        <a-form-item v-if="formData.id" field="id" label="ID">
          <a-input v-model="formData.id" disabled />
        </a-form-item>
        <template v-for="f in uiFields" :key="f.name">
          <a-form-item :field="f.name" :label="f.label" :rules="f.rules">
            <template v-if="f.type==='CharField'">
              <a-input v-model="formData[f.name]" :max-length="f.max_length || 255" allow-clear />
            </template>
            <template v-else-if="f.type==='TextField'">
              <a-textarea v-model="formData[f.name]" allow-clear :auto-size="{ minRows: 3 }" />
            </template>
            <template v-else-if="f.type==='IntegerField' || f.type==='PositiveIntegerField'">
              <a-input-number v-model="formData[f.name]" :min="f.type==='PositiveIntegerField' ? 0 : undefined" style="width: 100%" />
            </template>
            <template v-else-if="f.type==='DecimalField'">
              <a-input-number v-model="formData[f.name]" :precision="f.decimal_places || 2" :step="0.01" style="width: 100%" />
            </template>
            <template v-else-if="f.type==='BooleanField'">
              <a-switch v-model="formData[f.name]" />
            </template>
            <template v-else-if="f.type==='DateField'">
              <a-date-picker v-model="formData[f.name]" style="width: 100%" />
            </template>
            <template v-else-if="f.type==='DateTimeField'">
              <a-date-picker v-model="formData[f.name]" show-time style="width: 100%" />
            </template>
            <template v-else-if="f.type==='ForeignKey'">
              <a-input-number v-model="formData[f.name]" :min="1" placeholder="关联ID（可二开为下拉选择）" style="width: 100%" />
            </template>
            <template v-else>
              <a-input v-model="formData[f.name]" allow-clear />
            </template>
          </a-form-item>
        </template>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { getBookList, getBookDetail, createBook, updateBook, deleteBook } from '@/api/book'

// 由生成器注入的字段元数据（按后端模型定义）
const generatedFields = [
  {
    "name": "title",
    "type": "CharField",
    "verbose_name": "书名",
    "required": true,
    "unique": false,
    "max_length": 128
  },
  {
    "name": "author",
    "type": "CharField",
    "verbose_name": "作者",
    "required": false,
    "unique": false,
    "max_length": 64
  },
  {
    "name": "isbn",
    "type": "CharField",
    "verbose_name": "ISBN",
    "required": false,
    "unique": true,
    "max_length": 32
  },
  {
    "name": "price",
    "type": "DecimalField",
    "verbose_name": "价格",
    "required": false,
    "unique": false,
    "default": 0,
    "max_digits": 10,
    "decimal_places": 2
  },
  {
    "name": "published_date",
    "type": "DateField",
    "verbose_name": "出版日期",
    "required": false,
    "unique": false
  },
  {
    "name": "is_available",
    "type": "BooleanField",
    "verbose_name": "是否可借阅",
    "required": false,
    "unique": false,
    "default": true
  }
]

// 过滤掉审计/系统字段，仅生成业务字段
const hiddenFieldNames = new Set(['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'owner_organization', 'is_deleted', 'remark'])
const uiFields = generatedFields
  .filter(f => !hiddenFieldNames.has(f.name))
  .map(f => ({
    name: f.name,
    type: f.type,
    label: f.verbose_name || f.name,
    max_length: f.max_length,
    decimal_places: f.decimal_places,
    rules: f.required ? [{ required: true, message: `请填写${'$'}{f.verbose_name || f.name}` }] : []
  }))

const columns = [
  { title: 'ID', dataIndex: 'id', width: 100 },
  ...uiFields.map(f => ({ title: f.label, dataIndex: f.name })),
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
    const res = await getBookList({ page: pagination.current, page_size: pagination.pageSize, search: searchText.value || undefined })
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
  // 初始化业务字段默认值
  const init = { id: null }
  uiFields.forEach(f => {
    if (f.type === 'BooleanField') init[f.name] = false
    else init[f.name] = ''
  })
  Object.assign(formData, init)
  formVisible.value = true
}

const handleEdit = async (record) => {
  formTitle.value = '编辑'
  const res = await getBookDetail(record.id)
  const init = { id: res.id }
  uiFields.forEach(f => { init[f.name] = res[f.name] })
  Object.assign(formData, init)
  formVisible.value = true
}

const handleDelete = (record) => {
  Modal.confirm({
    title: '确认删除',
    onOk: async () => {
      await deleteBook(record.id)
      Message.success('删除成功')
      fetchData()
    }
  })
}

const handleSubmit = async () => {
  try {
    if (formData.id) {
      await updateBook(formData.id, formData)
      Message.success('更新成功')
    } else {
      await createBook(formData)
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

