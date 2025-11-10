import router, { addDynamicRoutes } from '@/router'
import store from '@/store'
import { Message } from '@arco-design/web-vue'

// 标记是否已加载菜单
let menuLoaded = false

router.beforeEach(async (to, from, next) => {
  console.log('[auth] beforeEach enter:', { to: to.fullPath, from: from.fullPath, menuLoaded })
  // 登录页和发卡网直接放行（不需要登录）
  if (to.path === '/login' || to.path === '/shop') {
    if (to.path === '/login') {
      menuLoaded = false // 退出登录时重置
    }
    console.log('[auth] public page passthrough:', to.path)
    next()
    return
  }

  // 检查是否有用户信息
  const hasUserInfo = store.state.user.id
  
  if (!hasUserInfo) {
    // 尝试获取用户信息（验证 Session 是否有效）
    try {
      console.log('[auth] fetching user info...')
      const success = await store.dispatch('user/getUserInfo')
      console.log('[auth] user info result:', success, store.state.user)
      if (!success) {
        Message.info('请先登录')
        console.warn('[auth] no user, redirect -> /login')
        next('/login')
        return
      }
    } catch (e) {
    Message.info('请先登录')
    console.error('[auth] getUserInfo error:', e)
    next('/login')
    return
    }
  }

  // 如果还没加载菜单，则加载菜单并添加路由
  if (!menuLoaded) {
    try {
      console.log('[auth] loading menu tree...')
      const success = await store.dispatch('menu/getMenuTree')
      console.log('[auth] menu load result:', success)
      if (success) {
        const menuTree = store.state.menu.menuTree
        console.log('[auth] menuTree:', menuTree)
        if (menuTree && menuTree.length > 0) {
          console.log('[auth] addDynamicRoutes start')
          addDynamicRoutes(menuTree)
          console.log('[auth] addDynamicRoutes done')
          menuLoaded = true
          
          // 路由添加完成后，重新匹配当前路径
          // 如果当前路由是根路径或找不到匹配的路由，重定向到第一个菜单
          if (to.path === '/' || to.path === '' || to.matched.length === 0) {
            const firstPath = findFirstMenuPath(menuTree)
            console.log('[auth] computed firstPath:', firstPath)
            if (firstPath) { next(firstPath); return }
          }
        }
      }
    } catch (e) {
      console.error('加载菜单失败:', e)
    }
  }

  // 如果路由匹配失败（404），且不是登录页，尝试重定向到第一个菜单
  if (to.matched.length === 0 && to.path !== '/login' && menuLoaded) {
    const menuTree = store.state.menu.menuTree
    if (menuTree && menuTree.length > 0) {
      const firstPath = findFirstMenuPath(menuTree)
      console.warn('[auth] 404 fallback -> firstPath:', firstPath)
      if (firstPath) { next(firstPath); return }
    }
  }

  console.log('[auth] beforeEach next() to:', to.fullPath)
  next()
})

/**
 * 查找第一个叶子菜单的完整路由路径（包含父级）
 */
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
  return p.replace(/^\/+|\/+$/g, '') // 去除首尾 '/'
}

function joinPath(parent, child) {
  const a = normalizePath(parent)
  const b = normalizePath(child)
  if (!a && !b) return '/'
  if (!a) return `/${b}`
  if (!b) return `/${a}`
  return `/${a}/${b}`
}
