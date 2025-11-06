<template>
  <div class="profile-page">
    <a-page-header title="个人中心" subtitle="查看个人信息并修改密码" />

    <a-grid :cols="24" :col-gap="16">
      <a-grid-item :span="8">
        <a-card title="基本信息">
          <a-descriptions :column="1" bordered>
            <a-descriptions-item label="用户名">{{ user.username }}</a-descriptions-item>
            <a-descriptions-item label="邮箱">{{ user.email || '-' }}</a-descriptions-item>
            <a-descriptions-item label="是否超管">{{ user.is_superuser ? '是' : '否' }}</a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-grid-item>
      <a-grid-item :span="16">
        <a-card title="修改密码">
          <a-form :model="pwd" :rules="rules" ref="formRef" layout="vertical">
            <a-form-item field="old_password" label="旧密码" required>
              <a-input-password v-model="pwd.old_password" placeholder="请输入旧密码" allow-clear />
            </a-form-item>
            <a-form-item field="new_password" label="新密码" required>
              <a-input-password v-model="pwd.new_password" placeholder="至少6位" allow-clear />
            </a-form-item>
            <a-space>
              <a-button type="primary" :loading="saving" @click="onSubmit">保存</a-button>
              <a-button @click="onReset">重置</a-button>
            </a-space>
          </a-form>
        </a-card>
      </a-grid-item>
    </a-grid>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getUserInfo, changePassword } from '@/api/user'

const user = reactive({ username: '', email: '', is_superuser: false })
const pwd = reactive({ old_password: '', new_password: '' })
const saving = ref(false)
const formRef = ref(null)

const rules = {
  old_password: [{ required: true, message: '请输入旧密码' }],
  new_password: [
    { required: true, message: '请输入新密码' },
    { minLength: 6, message: '新密码至少6位' },
  ],
}

async function loadUser() {
  try {
    const res = await getUserInfo()
    const data = res.data || res
    user.username = data.username || ''
    user.email = data.email || ''
    user.is_superuser = !!data.is_superuser
  } catch (e) {
    Message.error('获取用户信息失败')
  }
}

async function onSubmit() {
  try {
    const valid = await formRef.value.validate()
    if (valid) return
  } catch {}
  saving.value = true
  try {
    await changePassword({ ...pwd })
    Message.success('密码修改成功')
    onReset()
  } catch (e) {
    Message.error((e && e.message) || '修改失败')
  } finally {
    saving.value = false
  }
}

function onReset() {
  pwd.old_password = ''
  pwd.new_password = ''
}

onMounted(loadUser)
</script>

<style scoped>
.profile-page {
  padding: 16px;
}
</style>


