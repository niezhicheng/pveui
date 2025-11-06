<template>
  <div class="login">
    <div class="login-form">
      <div class="login-form-title">Django Vue AdminX 登录</div>

      <a-form
        ref="loginForm"
        :model="userInfo"
        layout="vertical"
        @submit="handleSubmit"
      >
        <a-form-item
          field="username"
          :rules="[{ required: true, message: '用户名不能为空' }]"
          :validate-trigger="['change', 'blur']"
          hide-label
        >
          <a-input v-model="userInfo.username" placeholder="用户名：admin" @keyup.enter="handleSubmit">
            <template #prefix>
              <icon-user />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item
          field="password"
          :rules="[{ required: true, message: '密码不能为空' }]"
          :validate-trigger="['change', 'blur']"
          hide-label
        >
          <a-input v-model="userInfo.password" placeholder="密码：admin123" type="password" @keyup.enter="handleSubmit">
            <template #prefix>
              <icon-lock />
            </template>
          </a-input>
        </a-form-item>

        <a-space :size="16" direction="vertical">
          <div class="login-form-password-actions">
            <a-checkbox v-model="rememberPassword">
              记住密码
            </a-checkbox>
          </div>
          <a-button type="primary" html-type="submit" long :loading="loading">
            登录
          </a-button>
        </a-space>
      </a-form>
    </div>
  </div>
</template>

<script setup>
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { reactive, ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import useLoading from '@/hooks/loading'

const userInfo = reactive({
  username: 'admin',
  password: 'admin123',
})
const { loading, setLoading } = useLoading()

const store = useStore()
const router = useRouter()

const rememberPassword = ref(false)

const handleSubmit = async () => {
  console.log('[login] submit start', JSON.parse(JSON.stringify(userInfo)))
  setLoading(true)
  const result = await store.dispatch('user/login', userInfo)
  setLoading(false)

  if (result) {
    // 登录成功后立刻拉取用户信息，填充 user.id，避免守卫再次跳回登录
    const ok = await store.dispatch('user/getUserInfo')
    console.log('[login] getUserInfo ok:', ok, store.state.user)
    if (!ok) return
    // 主动拉菜单并计算第一个可访问路径，直接跳转
    const menuOk = await store.dispatch('menu/getMenuTree')
    const menuTree = store.state.menu.menuTree || []
    console.log('[login] menu loaded:', menuOk, menuTree)
    const firstPath = findFirstMenuPath(menuTree) || '/'
    console.log('[login] navigate to firstPath:', firstPath)
    await router.replace(firstPath)
    console.log('[login] replace to firstPath done')
  } else {
    Message.error('用户名或密码错误')
    console.warn('[login] login failed')
  }
}

function findFirstMenuPath(menuTree, parentPath = '') {
  for (const menu of menuTree) {
    const curr = normalizePath(menu.path)
    const full = joinPath(parentPath, curr)
    if (menu.children && menu.children.length > 0) {
      const found = findFirstMenuPath(menu.children, full)
      if (found) return found
    } else if (curr) {
      return full || '/'
    }
  }
  return null
}

function normalizePath(p) {
  if (!p) return ''
  return p.replace(/^\/+|\/+$/g, '')
}

function joinPath(parent, child) {
  const a = normalizePath(parent)
  const b = normalizePath(child)
  if (!a && !b) return '/'
  if (!a) return `/${b}`
  if (!b) return `/${a}`
  return `/${a}/${b}`
}
</script>

<style scoped>
.login {
  position: fixed;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center
}

.login-form {
  width: 352px;
  padding: 16px;
  background: white;
}

.login-form-title {
  color: var(--color-text-1);
  font-weight: 500;
  font-size: 24px;
  line-height: 32px;
  margin-bottom: 16px;
  text-align: center;
}

.login-form-password-actions {
  display: flex;
  justify-content: space-between;
}

.login-form-register-btn {
  color: var(--color-text-3) !important;
}
</style>
