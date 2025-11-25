<template>
  <a-menu
    v-if="menuTree.length > 0"
    :style="{ width: '220px', height: '100%', flexShrink: 0 }"
    :default-selected-keys="[openedMenu]"
    :auto-open="false"
    @menu-item-click="handleMenuClick"
    show-collapse-button
  >
    <sidebar-item v-for="menu in menuTree" :key="menu.id || menu.path" :item="menu" parent-path="" />
  </a-menu>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import SidebarItem from './sidebar-item'

const $router = useRouter()
const $store = useStore()

// 从 store 获取菜单树
const menuTree = computed(() => $store.state.menu.menuTree || [])

const openedMenu = computed(() => $router.currentRoute.value.path)

const handleMenuClick = (key) => {
  // key 是路由名称（如 system_user）
  // 优先使用命名路由跳转
  $router.push({ name: key }).catch((err) => {
    console.warn('命名路由跳转失败，尝试使用完整路径:', key, err)
    // 如果命名路由失败，从路由名称反推完整路径
    // system_user -> /system/user
    const path = '/' + key.replace(/_/g, '/')
    $router.push(path).catch(() => {
      console.error('路由跳转失败:', key, path)
    })
  })
}
</script>
