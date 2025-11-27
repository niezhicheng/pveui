<template>
  <div class="container">
    <div class="stage">
      <div class="banner">
      <div class="banner-inner">
        <a-carousel class="carousel" animation-name="fade" indicator-type="line" :autoplay="true">
          <a-carousel-item v-for="item in carouselItems" :key="item.slogan">
            <div class="carousel-item">
              <div class="carousel-title">{{ item.slogan }}</div>
              <div class="carousel-sub-title">{{ item.subSlogan }}</div>
              <img class="carousel-image" :src="item.image" />
            </div>
          </a-carousel-item>
        </a-carousel>
      </div>
      </div>

      <div class="content">
        <div class="content-inner">
          <div class="logo">
            <img alt="logo" src="/icon.svg" />
            <div class="logo-text">pve-ui</div>
          </div>

          <div class="login-form-wrapper">
            <div class="login-form-title">欢迎登录</div>
            <div class="login-form-sub-title">使用管理员账号进入系统</div>
            <div class="login-form-error-msg"></div>

            <a-form ref="loginForm" :model="userInfo" class="login-form" layout="vertical" @submit="handleSubmit">
              <a-form-item field="username" :rules="[{ required: true, message: '用户名不能为空' }]" :validate-trigger="['change', 'blur']" hide-label>
                <a-input v-model="userInfo.username" placeholder="用户名：admin" @keyup.enter="handleSubmit">
                  <template #prefix><icon-user /></template>
                </a-input>
              </a-form-item>

              <a-form-item field="password" :rules="[{ required: true, message: '密码不能为空' }]" :validate-trigger="['change', 'blur']" hide-label>
                <a-input-password v-model="userInfo.password" placeholder="密码：admin123" allow-clear @keyup.enter="handleSubmit">
                  <template #prefix><icon-lock /></template>
                </a-input-password>
              </a-form-item>

              <a-space :size="16" direction="vertical">
                <div class="login-form-password-actions">
                  <a-checkbox v-model="rememberPassword">记住密码</a-checkbox>
                </div>
                <a-button type="primary" html-type="submit" long :loading="loading">登录</a-button>
              </a-space>
            </a-form>
          </div>

          <div class="footer">
            <div class="copyright">© {{ new Date().getFullYear() }} pve-ui</div>
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

// 左侧轮播数据
const carouselItems = [
  {
    slogan: '开箱即用的高质量模板',
    subSlogan: '覆盖常见业务场景，提升开发效率',
    image: 'https://vuejs-core.cn/vue-admin-arco/static/png/login-banner-Cqtv5-d6.png',
  },
  {
    slogan: '极简架构 · 清晰分层',
    subSlogan: '后端 DRF + 前端 Vue3 + Arco Design',
    image: 'https://vuejs-core.cn/vue-admin-arco/static/png/login-banner-Cqtv5-d6.png',
  },
  {
    slogan: 'RBAC 权限 · 代码生成器',
    subSlogan: '权限到按钮级，CRUD 一键生成',
    image: 'https://vuejs-core.cn/vue-admin-arco/static/png/login-banner-Cqtv5-d6.png',
  },
]

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
.container { display: flex; height: 100vh; background: linear-gradient(135deg, #F5F7FF 0%, #F7FBFF 100%); }
.stage { width: 100vw; height: 100vh; display: grid; grid-template-columns: 25% 1fr; gap: 0; }
.banner { background: linear-gradient(163.85deg, #1d2129 0%, #00308f 100%); color: #fff; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.banner-inner { flex: 1; height: 100%; padding: 24px; }
.carousel { height: 100%; }
.carousel-item { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; }
.carousel-title { color: #EFF4FF; font-weight: 600; font-size: 20px; line-height: 28px; }
.carousel-sub-title { margin-top: 8px; color: rgba(255,255,255,0.7); font-size: 14px; line-height: 22px; }
.carousel-image { width: 320px; margin-top: 30px; }

.content { position: relative; display: flex; align-items: center; justify-content: center; padding: 20px 24px; }
.content-inner { width: clamp(360px, 26vw, 520px); }
.logo { display: inline-flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.logo img { width: 24px; height: 24px; }
.logo-text { color: #1d2129; font-size: 18px; font-weight: 600; }

.login-form-wrapper { width: 100%; }
.login-form-title { color: #1d2129; font-weight: 600; font-size: 22px; line-height: 30px; }
.login-form-sub-title { color: #86909c; font-size: 14px; line-height: 22px; }
.login-form-error-msg { height: 28px; color: rgb(var(--red-6)); line-height: 28px; }
.login-form-password-actions { display: flex; justify-content: space-between; }

/* 输入背景弱化 */
:deep(.arco-input), :deep(.arco-input-wrapper) { background: #f2f3f5; }

.footer { margin-top: 12px; width: 100%; text-align: center; color: #86909c; font-size: 12px; }

@media (max-width: 920px) {
  .stage { width: 92vw; height: auto; min-width: 0; grid-template-columns: 1fr; }
  .banner { display: none; }
  .content { border-radius: 16px; }
  .content-inner { width: 90vw; max-width: 520px; }
}
</style>
