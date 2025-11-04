<template>
  <div class="codegen-page">
    <a-card>
      <template #title>
        <a-typography-title :heading="4">代码生成器（可视化定义字段 → 一键生成）</a-typography-title>
      </template>

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
import { ref, reactive } from 'vue'
import { Message } from '@arco-design/web-vue'
import { submitCodegen } from '@/api/codegen'

const form = reactive({ app_label: 'curdexample', model_name: 'Book', module_path: 'system/book', enhanced_data_scope: true })
const submitting = ref(false)

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

const fields = ref([
])

function addField() {
  fields.value.push({
    _id: nextId(),
    name: '',
    verbose_name: '',
    type: 'CharField',
    required: true,
    unique: false,
    default: '',
    max_length: 128,
    max_digits: 10,
    decimal_places: 2,
    related_app: '',
    related_model: '',
  })
}

function addPresetBook() {
  fields.value = [
    { _id: nextId(), name: 'title', verbose_name: '书名', type: 'CharField', required: true, unique: false, default: '', max_length: 128 },
    { _id: nextId(), name: 'author', verbose_name: '作者', type: 'CharField', required: false, unique: false, default: '', max_length: 64 },
    { _id: nextId(), name: 'isbn', verbose_name: 'ISBN', type: 'CharField', required: false, unique: true, default: '', max_length: 32 },
    { _id: nextId(), name: 'price', verbose_name: '价格', type: 'DecimalField', required: false, unique: false, default: 0, max_digits: 10, decimal_places: 2 },
    { _id: nextId(), name: 'published_date', verbose_name: '出版日期', type: 'DateField', required: false, unique: false, default: '' },
    { _id: nextId(), name: 'is_available', verbose_name: '是否可借阅', type: 'BooleanField', required: false, unique: false, default: true },
  ]
}

function clearFields() {
  fields.value = []
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

const handleGenerate = async () => {
  if (!validateForm()) return
  submitting.value = true
  try {
    const payload = buildPayload()
    await submitCodegen(payload)
    Message.success('已提交生成任务（查看后端产物/.gen 文件）')
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
</style>

