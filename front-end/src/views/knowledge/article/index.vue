<template>
  <div class="knowledge-page">
    <a-card>
      <template #title>
        <a-typography-title :heading="5">知识库</a-typography-title>
      </template>

      <div class="toolbar">
        <a-space>
          <a-button type="primary" @click="handleCreate">
            <template #icon>
              <icon-plus />
            </template>
            新建文章
          </a-button>
          <a-input-search
            v-model="searchText"
            placeholder="搜索标题、标签或内容"
            style="width: 240px"
            allow-clear
            @search="fetchList"
            @clear="fetchList"
          />
          <a-select
            v-model="filters.category"
            placeholder="选择分类"
            style="width: 160px"
            allow-clear
            @change="handleFilterChange"
          >
            <a-option v-for="item in categoryOptions" :key="item.value" :value="item.value">
              {{ item.label }}
            </a-option>
          </a-select>
          <a-select
            v-model="filters.is_published"
            placeholder="发布状态"
            style="width: 140px"
            allow-clear
            @change="handleFilterChange"
          >
            <a-option :value="true">已发布</a-option>
            <a-option :value="false">草稿</a-option>
          </a-select>
        </a-space>
      </div>

      <a-table
        :data="tableData"
        :loading="loading"
        row-key="id"
        :pagination="pagination"
        @page-change="handlePageChange"
        @page-size-change="handlePageSizeChange"
      >
        <template #columns>
          <a-table-column title="标题" data-index="title" />
          <a-table-column title="分类" data-index="category">
            <template #cell="{ record }">
              {{ getCategoryLabel(record.category) }}
            </template>
          </a-table-column>
          <a-table-column title="标签" data-index="tags">
            <template #cell="{ record }">
              <a-space wrap>
                <a-tag v-for="tag in parseTags(record.tags)" :key="tag" color="arcoblue">
                  {{ tag }}
                </a-tag>
              </a-space>
            </template>
          </a-table-column>
          <a-table-column title="状态" data-index="is_published">
            <template #cell="{ record }">
              <a-tag :color="record.is_published ? 'green' : 'gray'">
                {{ record.is_published ? '已发布' : '草稿' }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="置顶" data-index="is_pinned">
            <template #cell="{ record }">
              <a-tag :color="record.is_pinned ? 'gold' : 'blue'">
                {{ record.is_pinned ? '置顶' : '普通' }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="更新时间" data-index="updated_at">
            <template #cell="{ record }">
              {{ formatDate(record.updated_at) }}
            </template>
          </a-table-column>
          <a-table-column title="操作" :width="210">
            <template #cell="{ record }">
              <a-space :size="8">
                <a-button type="text" size="small" @click="handlePreview(record)">预览</a-button>
                <a-button type="text" size="small" @click="handleEdit(record)">编辑</a-button>
                <a-button type="text" size="small" status="danger" @click="handleDelete(record)">删除</a-button>
              </a-space>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:visible="editorVisible"
      :title="currentId ? '编辑文章' : '新建文章'"
      :fullscreen="true"
      :footer="false"
    >
      <div class="editor-wrapper">
        <a-space direction="vertical" style="width: 100%">
          <a-input v-model="form.title" placeholder="请输入标题" allow-clear size="large" />
          <a-textarea
            v-model="form.summary"
            placeholder="请输入摘要"
            :auto-size="{ minRows: 2, maxRows: 4 }"
          />
          <a-select v-model="form.category" placeholder="请选择分类">
            <a-option v-for="item in categoryOptions" :key="item.value" :value="item.value">
              {{ item.label }}
            </a-option>
          </a-select>
          <a-input v-model="form.tags" placeholder="标签（逗号分隔）" allow-clear />

          <div class="editor-status">
            <a-space>
              <span>发布状态</span>
              <a-switch v-model="form.is_published" checked-text="已发布" unchecked-text="草稿" />
            </a-space>
            <a-space>
              <span>置顶</span>
              <a-switch v-model="form.is_pinned" />
            </a-space>
          </div>

          <div class="rich-editor">
            <Toolbar :editor="editorRef" :default-config="toolbarConfig" :mode="editorMode" />
            <Editor
              v-model="editorHtml"
              :default-config="editorConfig"
              :mode="editorMode"
              @onCreated="handleEditorCreated"
            />
          </div>

          <div class="editor-footer">
            <a-space style="margin-left: auto">
              <a-button @click="editorVisible = false">关闭</a-button>
              <a-button type="primary" :loading="saving" @click="handleSave">保存</a-button>
            </a-space>
          </div>
        </a-space>
      </div>
    </a-modal>

    <a-modal v-model:visible="previewVisible" :title="previewData.title" :width="900" :footer="false">
      <div class="preview-wrapper">
        <div class="preview-meta">
          <a-space>
            <a-tag>{{ getCategoryLabel(previewData.category) }}</a-tag>
            <a-tag :color="previewData.is_published ? 'green' : 'gray'">
              {{ previewData.is_published ? '已发布' : '草稿' }}
            </a-tag>
            <a-tag v-if="previewData.is_pinned" color="gold">置顶</a-tag>
          </a-space>
          <div class="preview-time">更新时间：{{ formatDate(previewData.updated_at) }}</div>
        </div>
        <div class="preview-content" v-html="previewData.content"></div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, shallowRef } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { IconPlus } from '@arco-design/web-vue/es/icon'
import '@wangeditor/editor/dist/css/style.css'
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'
import {
  getKnowledgeList,
  getKnowledgeDetail,
  createKnowledge,
  updateKnowledge,
  deleteKnowledge,
  getKnowledgeCategories,
} from '@/api/knowledge'

const loading = ref(false)
const searchText = ref('')
const tableData = ref([])
const categoryOptions = ref([])

const filters = reactive({
  category: '',
  is_published: undefined,
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showTotal: true,
  showPageSize: true,
})

const editorVisible = ref(false)
const previewVisible = ref(false)
const saving = ref(false)
const currentId = ref(null)
const previewData = reactive({
  title: '',
  category: '',
  is_published: true,
  is_pinned: false,
  updated_at: '',
  content: '',
})

const form = reactive({
  title: '',
  summary: '',
  category: '',
  tags: '',
  is_published: true,
  is_pinned: false,
})

const editorRef = shallowRef(null)
const editorHtml = ref('')
const editorMode = 'default'
const toolbarConfig = {}
const editorConfig = { placeholder: '请输入文章内容...' }

const handleEditorCreated = (editor) => {
  editorRef.value = editor
}

onBeforeUnmount(() => {
  const editor = editorRef.value
  if (editor == null) return
  editor.destroy()
})

function parseTags(tags) {
  if (!tags) return []
  return tags
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
}

function getCategoryLabel(value) {
  const match = categoryOptions.value.find((item) => item.value === value)
  return match ? match.label : value || '-'
}

function formatDate(value) {
  if (!value) return '-'
  try {
    const d = new Date(value)
    if (Number.isNaN(d.getTime())) return value
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
      d.getDate(),
    ).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(
      d.getMinutes(),
    ).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
  } catch (e) {
    return value
  }
}

async function fetchCategories() {
  try {
    const res = await getKnowledgeCategories()
    categoryOptions.value = Array.isArray(res) ? res : res.data || []
  } catch (e) {
    categoryOptions.value = []
  }
}

async function fetchList() {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
    }
    if (searchText.value) params.search = searchText.value
    if (filters.category) params.category = filters.category
    if (typeof filters.is_published === 'boolean') params.is_published = filters.is_published

    const res = await getKnowledgeList(params)
    const data = res
    if (Array.isArray(data.results)) {
      tableData.value = data.results
      pagination.total = data.count || data.results.length
    } else if (Array.isArray(data)) {
      tableData.value = data
      pagination.total = data.length
    } else {
      tableData.value = []
      pagination.total = 0
    }
  } catch (e) {
    Message.error('获取知识库列表失败：' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

function handlePageChange(page) {
  pagination.current = page
  fetchList()
}

function handlePageSizeChange(size) {
  pagination.pageSize = size
  pagination.current = 1
  fetchList()
}

function handleFilterChange() {
  pagination.current = 1
  fetchList()
}

function resetForm() {
  form.title = ''
  form.summary = ''
  form.category = ''
  form.tags = ''
  form.is_published = true
  form.is_pinned = false
  editorHtml.value = ''
  currentId.value = null
}

function handleCreate() {
  resetForm()
  editorVisible.value = true
}

async function handleEdit(record) {
  try {
    const res = await getKnowledgeDetail(record.id)
    const data = res
    currentId.value = data.id
    form.title = data.title || ''
    form.summary = data.summary || ''
    form.category = data.category || ''
    form.tags = data.tags || ''
    form.is_published = !!data.is_published
    form.is_pinned = !!data.is_pinned
    editorHtml.value = data.content || ''
    editorVisible.value = true
  } catch (e) {
    Message.error('获取文章详情失败：' + (e.message || '未知错误'))
  }
}

async function handlePreview(record) {
  try {
    const res = await getKnowledgeDetail(record.id)
    Object.assign(previewData, {
      title: res.title,
      category: res.category,
      is_published: res.is_published,
      is_pinned: res.is_pinned,
      updated_at: res.updated_at,
      content: res.content,
    })
    previewVisible.value = true
  } catch (e) {
    Message.error('预览失败：' + (e.message || '未知错误'))
  }
}

async function handleSave() {
  if (!form.title) {
    Message.warning('请输入标题')
    return
  }
  if (!editorHtml.value) {
    Message.warning('请输入文章内容')
    return
  }

  saving.value = true
  try {
    const payload = {
      title: form.title,
      summary: form.summary,
      category: form.category,
      tags: form.tags,
      is_published: form.is_published,
      is_pinned: form.is_pinned,
      content: editorHtml.value,
    }
    if (currentId.value) {
      await updateKnowledge(currentId.value, payload)
      Message.success('更新成功')
    } else {
      await createKnowledge(payload)
      Message.success('创建成功')
    }
    editorVisible.value = false
    fetchList()
  } catch (e) {
    Message.error('保存失败：' + (e.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

function handleDelete(record) {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除文章「${record.title}」吗？`,
    onOk: async () => {
      try {
        await deleteKnowledge(record.id)
        Message.success('删除成功')
        fetchList()
      } catch (e) {
        Message.error('删除失败：' + (e.message || '未知错误'))
      }
    },
  })
}

onMounted(() => {
  fetchCategories()
  fetchList()
})
</script>

<style scoped>
.knowledge-page {
  padding: 20px;
}

.toolbar {
  margin-bottom: 12px;
}

.editor-wrapper {
  padding: 12px 0;
}

.editor-status {
  display: flex;
  gap: 24px;
  align-items: center;
}

.rich-editor {
  border: 1px solid #e5e6eb;
}

.preview-wrapper {
  padding: 12px 0;
}

.preview-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.preview-content {
  background: #fafafa;
  padding: 16px;
  border-radius: 4px;
  min-height: 200px;
}
</style>
