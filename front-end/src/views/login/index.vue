<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-left">
        <div class="banner">
          <div class="banner-head">
            <img class="mini-logo" src="/icon.svg" alt="logo" />
            <span class="banner-title">Django Vue AdminX</span>
          </div>
          <div class="banner-sub">开箱即用的高质量模板</div>

          <div class="form-wrapper">
            <div class="form-header">
              <div class="title">欢迎登录</div>
              <div class="subtitle">使用管理员账号进入系统</div>
            </div>

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
                <a-input v-model="userInfo.username" placeholder="用户名：admin" size="large" @keyup.enter="handleSubmit">
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
                <a-input v-model="userInfo.password" placeholder="密码：admin123" type="password" size="large" @keyup.enter="handleSubmit">
                  <template #prefix>
                    <icon-lock />
                  </template>
                </a-input>
              </a-form-item>

              <div class="actions">
                <a-checkbox v-model="rememberPassword">记住密码</a-checkbox>
              </div>

              <a-button type="primary" html-type="submit" long size="large" :loading="loading">
                登录
              </a-button>
            </a-form>
          </div>
        </div>
      </div>
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
.login-page {
  position: fixed;
  inset: 0;
  background: linear-gradient(135deg, #F5F7FF 0%, #F7FBFF 100%);
}

.login-container {
  display: grid;
  grid-template-columns: 640px;
  gap: 0;
  height: 100%;
  align-items: center;
  max-width: 680px;
  margin: 0 auto;
  padding: 16px 20px;
}

.login-left {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.banner {
  background: radial-gradient(120px 120px at 20% 20%, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0) 100%),
              linear-gradient(135deg, #0B2B6B 0%, #0F3B9E 50%, #0B2B6B 100%);
  color: #fff;
  padding: 18px;
  border-radius: 14px;
  min-height: 420px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 16px 40px rgba(5, 17, 54, 0.25);
}

.banner-head {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: rgba(255,255,255,0.12);
  border-radius: 999px;
  padding: 6px 12px;
  width: fit-content;
}

.mini-logo { width: 20px; height: 20px; }
.banner-title { font-weight: 600; }
.banner-sub { margin-top: 16px; opacity: 0.85; }

.form-wrapper {
  margin-top: 18px;
  background: #ffffff;
  color: #1d2129;
  border-radius: 10px;
  padding: 16px 16px 18px;
  box-shadow: 0 8px 24px rgba(31,35,41,0.12);
  width: 420px;
  align-self: center;
}

/* 移除了右侧卡片布局（表单合入左侧 banner） */

.form-header .title {
  font-size: 22px;
  font-weight: 600;
  color: #1d2129;
}

.form-header .subtitle {
  margin-top: 6px;
  color: #86909c;
}

.actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 12px 0 16px;
}

/* 输入背景弱化，更像示例 */
:deep(.arco-input) {
  background: #f2f3f5;
}

@media (max-width: 920px) {
  .login-container {
    grid-template-columns: 1fr;
    max-width: 480px;
  }
  .login-left { display: none; }
}
</style>
