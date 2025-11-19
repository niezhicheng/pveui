<template>
  <div class="codegen-page">
    <a-card>
      <template #title>
        <a-typography-title :heading="4">代码生成器（可视化定义字段 → 一键生成）</a-typography-title>
      </template>

      <a-alert type="warning" closable style="margin-bottom: 12px;">
        <template #title>生成后请在后端执行数据库迁移</template>
        <div>
          为使新增模型同步到数据库，请在 <code>backend</code> 目录执行：
          <pre style="background:#f6f8fa;padding:8px;border-radius:6px;overflow:auto;margin-top:6px;">
python manage.py makemigrations
python manage.py migrate
          </pre>
        </div>
      </a-alert>

      <a-form layout="vertical" style="width: 100%">
        <a-space size="large" direction="vertical" fill>
          <a-grid :cols="4" :col-gap="16">
            <a-grid-item>
              <a-form-item label="应用标识 app_label">
                <a-input v-model="form.app_label" placeholder="例如：curdexample" />
              </a-form-item>
            </a-grid-item>
            <a-grid-item>
              <a-form-item label="模型名 model_name">
                <a-input v-model="form.model_name" placeholder="例如：Book" />
              </a-form-item>
            </a-grid-item>
            <a-grid-item>
              <a-form-item label="前端模块路径 module_path">
                <a-input v-model="form.module_path" placeholder="例如：system/book" />
              </a-form-item>
            </a-grid-item>
            <a-grid-item>
              <a-form-item label="增强数据权限控制">
                <a-switch v-model="form.enhanced_data_scope" checked-text="开启" unchecked-text="关闭" />
              </a-form-item>
            </a-grid-item>
          </a-grid>

          <a-card class="ai-box" size="small">
            <a-space direction="vertical" fill>
              <div class="ai-box__header">
                <a-typography-title :heading="5">AI 辅助建表</a-typography-title>
                <a-tag color="arcoblue" bordered>实验特性</a-tag>
              </div>
              <a-typography-text type="secondary">
                描述业务实体的用途、关键字段或约束，AI 将自动生成符合本工具格式的 JSON 并回填。
              </a-typography-text>
              <a-textarea
                v-model="aiPrompt"
                placeholder="例如：我要管理图书馆藏，包含书名、作者、ISBN、价格、出版日期、是否可借阅等字段"
                allow-clear
                :auto-size="{ minRows: 3, maxRows: 6 }"
              />
              <a-space align="center">
                <a-button type="outline" :loading="aiLoading" @click="handleAiGenerate">AI 生成字段</a-button>
                <a-typography-text type="secondary">生成后可继续调整字段，满意后再点击“生成代码”</a-typography-text>
              </a-space>
              <a-alert v-if="aiSummary" type="success" closable @close="aiSummary = ''">
                <template #title>AI 建表建议</template>
                <div>{{ aiSummary }}</div>
              </a-alert>
            </a-space>
          </a-card>

          <div class="toolbar">
            <a-space>
              <a-button type="primary" @click="addField">新增字段</a-button>
              <a-button @click="addPresetBook">填充图书示例</a-button>
              <a-button status="warning" @click="clearFields">清空</a-button>
            </a-space>
          </div>

          <a-table :data="fields" :pagination="false" row-key="_id" :bordered="false" size="small">
            <template #columns>
              <a-table-column title="#" :width="62">
                <template #cell="{ rowIndex }">
                  <a-space>
                    <a-button size="mini" @click="moveUp(rowIndex)" :disabled="rowIndex===0">上移</a-button>
                    <a-button size="mini" @click="moveDown(rowIndex)" :disabled="rowIndex===fields.length-1">下移</a-button>
                  </a-space>
                </template>
              </a-table-column>
              <a-table-column title="字段名" :width="180">
                <template #cell="{ record }">
                  <a-input v-model="record.name" placeholder="如：title" />
                </template>
              </a-table-column>
              <a-table-column title="显示名" :width="180">
                <template #cell="{ record }">
                  <a-input v-model="record.verbose_name" placeholder="如：书名" />
                </template>
              </a-table-column>
              <a-table-column title="类型" :width="200">
                <template #cell="{ record }">
                  <a-select v-model="record.type" :options="typeOptions" @change="() => onTypeChange(record)" />
                </template>
              </a-table-column>
              <a-table-column title="参数" :width="360">
                <template #cell="{ record }">
                  <div class="param-row">
                    <template v-if="record.type==='CharField'">
                      <a-input-number v-model="record.max_length" :min="1" :max="10240" placeholder="max_length" style="width: 140px" />
                    </template>
                    <template v-else-if="record.type==='DecimalField'">
                      <a-input-number v-model="record.max_digits" :min="1" :max="20" placeholder="max_digits" style="width: 140px" />
                      <a-input-number v-model="record.decimal_places" :min="0" :max="10" placeholder="decimal_places" style="width: 160px" />
                    </template>
                    <template v-else-if="record.type==='ForeignKey'">
                      <a-input v-model="record.related_app" placeholder="关联应用，如 rbac" style="width: 160px" />
                      <a-input v-model="record.related_model" placeholder="关联模型，如 User" style="width: 160px" />
                    </template>
                    <template v-else>
                      <a-typography-text type="secondary">无</a-typography-text>
                    </template>
                  </div>
                </template>
              </a-table-column>
              <a-table-column title="选项" :width="260">
                <template #cell="{ record }">
                  <a-space wrap>
                    <a-switch v-model="record.required" checked-text="必填" unchecked-text="可空" />
                    <a-switch v-model="record.unique" checked-text="唯一" unchecked-text="可重复" />
                    <a-input v-model="record.default" placeholder="默认值" style="width: 120px" />
                  </a-space>
                </template>
              </a-table-column>
              <a-table-column title="操作" :width="100" align="center">
                <template #cell="{ rowIndex }">
                  <a-button status="danger" size="mini" @click="removeField(rowIndex)">删除</a-button>
                </template>
              </a-table-column>
            </template>
          </a-table>

          <a-divider />

          <a-space>
            <a-button type="primary" :loading="submitting" @click="handleGenerate">生成代码</a-button>
          </a-space>
        </a-space>
      </a-form>
    </a-card>
  </div>
  </template>

<script setup>
import { ref, reactive, h } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { submitCodegen, generateSchemaByAI } from '@/api/codegen'

const form = reactive({ app_label: 'curdexample', model_name: 'Book', module_path: 'system/book', enhanced_data_scope: true })
const submitting = ref(false)
const aiPrompt = ref('')
const aiSummary = ref('')
const aiLoading = ref(false)

let uid = 1
const nextId = () => uid++

const typeOptions = [
  { label: 'CharField', value: 'CharField' },
  { label: 'TextField', value: 'TextField' },
  { label: 'IntegerField', value: 'IntegerField' },
  { label: 'PositiveIntegerField', value: 'PositiveIntegerField' },
  { label: 'DecimalField', value: 'DecimalField' },
  { label: 'BooleanField', value: 'BooleanField' },
  { label: 'DateField', value: 'DateField' },
  { label: 'DateTimeField', value: 'DateTimeField' },
  { label: 'ForeignKey', value: 'ForeignKey' },
]

const fields = ref([])

function createFieldFromSchema(field = {}) {
  return {
    _id: nextId(),
    name: field.name || '',
    verbose_name: field.verbose_name || field.name || '',
    type: field.type || 'CharField',
    required: field.required !== undefined ? !!field.required : true,
    unique: field.unique !== undefined ? !!field.unique : false,
    default: field.default ?? '',
    max_length: field.max_length ?? 128,
    max_digits: field.max_digits ?? 10,
    decimal_places: field.decimal_places ?? 2,
    related_app: field.related_app || '',
    related_model: field.related_model || '',
  }
}

function addField() {
  fields.value.push(createFieldFromSchema())
}

function addPresetBook() {
  fields.value = [
    createFieldFromSchema({ name: 'title', verbose_name: '书名', type: 'CharField', required: true, max_length: 128 }),
    createFieldFromSchema({ name: 'author', verbose_name: '作者', type: 'CharField', required: false, max_length: 64 }),
    createFieldFromSchema({ name: 'isbn', verbose_name: 'ISBN', type: 'CharField', required: false, unique: true, max_length: 32 }),
    createFieldFromSchema({ name: 'price', verbose_name: '价格', type: 'DecimalField', required: false, default: 0, max_digits: 10, decimal_places: 2 }),
    createFieldFromSchema({ name: 'published_date', verbose_name: '出版日期', type: 'DateField', required: false }),
    createFieldFromSchema({ name: 'is_available', verbose_name: '是否可借阅', type: 'BooleanField', required: false, default: true }),
  ]
}

function clearFields() {
  fields.value = []
  aiSummary.value = ''
}

function removeField(index) {
  fields.value.splice(index, 1)
}

function moveUp(index) {
  if (index <= 0) return
  const arr = fields.value
  ;[arr[index - 1], arr[index]] = [arr[index], arr[index - 1]]
}

function moveDown(index) {
  if (index >= fields.value.length - 1) return
  const arr = fields.value
  ;[arr[index + 1], arr[index]] = [arr[index], arr[index + 1]]
}

function onTypeChange(record) {
  if (record.type === 'CharField' && !record.max_length) record.max_length = 128
  if (record.type === 'DecimalField') {
    if (!record.max_digits) record.max_digits = 10
    if (!record.decimal_places) record.decimal_places = 2
  }
}

function validateForm() {
  if (!form.app_label || !form.model_name || !form.module_path) {
    Message.error('请填写 app_label / model_name / module_path')
    return false
  }
  if (!fields.value.length) {
    Message.error('请至少新增一个字段')
    return false
  }
  for (const f of fields.value) {
    if (!f.name) { Message.error('存在未填写字段名'); return false }
    if (!f.type) { Message.error('存在未选择字段类型'); return false }
    if (f.type === 'CharField' && (!f.max_length || f.max_length <= 0)) { Message.error('CharField 需要 max_length'); return false }
    if (f.type === 'DecimalField') {
      if (!f.max_digits || f.max_digits <= 0) { Message.error('DecimalField 需要 max_digits'); return false }
      if (f.decimal_places == null || f.decimal_places < 0) { Message.error('DecimalField 需要 decimal_places'); return false }
    }
    if (f.type === 'ForeignKey' && (!f.related_app || !f.related_model)) { Message.error('ForeignKey 需要关联应用与模型'); return false }
  }
  return true
}

function buildPayload() {
  const cleaned = fields.value.map(f => {
    const o = {
      name: f.name,
      type: f.type,
      verbose_name: f.verbose_name || f.name,
      required: !!f.required,
      unique: !!f.unique,
    }
    if (f.default !== '' && f.default !== undefined) o.default = f.default
    if (f.type === 'CharField' && f.max_length) o.max_length = f.max_length
    if (f.type === 'DecimalField') {
      o.max_digits = f.max_digits
      o.decimal_places = f.decimal_places
    }
    if (f.type === 'ForeignKey') {
      o.related_app = f.related_app
      o.related_model = f.related_model
    }
    return o
  })
  return {
    app_label: form.app_label,
    model_name: form.model_name,
    module_path: form.module_path,
    enhanced_data_scope: !!form.enhanced_data_scope,
    fields: cleaned,
  }
}

function applySchemaFromAI(schema) {
  if (!schema) return
  if (schema.app_label) form.app_label = schema.app_label
  if (schema.model_name) form.model_name = schema.model_name
  if (schema.module_path) form.module_path = schema.module_path
  if (Array.isArray(schema.fields) && schema.fields.length) {
    fields.value = schema.fields.map(item => createFieldFromSchema(item))
  }
  aiSummary.value = schema.summary || ''
}

const handleAiGenerate = async () => {
  const prompt = aiPrompt.value.trim()
  if (!prompt) {
    Message.warning('请先输入业务描述')
    return
  }
  aiLoading.value = true
  try {
    const schema = await generateSchemaByAI({
      prompt,
      app_label: form.app_label,
      model_name: form.model_name,
      module_path: form.module_path,
    })
    applySchemaFromAI(schema)
    Message.success('AI 已生成字段，可继续调整后提交')
  } catch (error) {
    const detail = error?.response?.data?.detail || error?.message || 'AI 生成失败'
    Message.error(detail)
  } finally {
    aiLoading.value = false
  }
}

const handleGenerate = async () => {
  if (!validateForm()) return
  submitting.value = true
  try {
    const payload = buildPayload()
    await submitCodegen(payload)
    Modal.success({
      title: '生成成功 - 请执行数据库迁移',
      content: () => h('div', { style: 'line-height:1.6' }, [
        h('p', '后端模型已生成，为使数据库生效，请在 backend 目录执行：'),
        h('pre', { style: 'background:#f6f8fa;padding:8px;border-radius:6px;overflow:auto' }, 'python manage.py makemigrations\npython manage.py migrate'),
        h('p', '完成后刷新页面即可使用。')
      ]),
      okText: '我已执行迁移，刷新',
      onOk: () => { window.location.reload() },
    })
  } catch (e) {
    Message.error('生成失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.codegen-page { padding: 20px; }
.toolbar { display: flex; justify-content: space-between; align-items: center; }
.param-row { display: flex; gap: 8px; align-items: center; }
.ai-box { background: #fafbff; }
.ai-box__header { display: flex; align-items: center; gap: 8px; }
</style>

