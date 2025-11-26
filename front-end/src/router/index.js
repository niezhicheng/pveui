import Layout from '@/layout/content'
import { createRouter, createWebHashHistory } from "vue-router"
import { menuTreeToRoutes } from '@/utils/menu'

// 基础路由（不需要权限）
export const constantRoutes = [
  {
    path: '/404',
    component: () => import('@/views/404'),
    hidden: true
  },

  {
    path: '/login',
    component: () => import('@/views/login'),
    hidden: true
  },
  // 发卡网前台（不需要登录）
  {
    path: '/shop',
    component: () => import('@/views/shop/index.vue'),
    hidden: true
  },
  // 初始根路径占位，避免在动态路由注入前访问 '/' 报错
  {
    name: 'rootRedirect',
    path: '/',
    redirect: '/login',
    hidden: true
  },
  // 个人中心（常量路由，不随菜单控制）
  {
    path: '/profile',
    component: Layout,
    hidden: true,
    children: [
      {
        path: '',
        component: () => import('@/views/system/profile/index.vue'),
        hidden: true
      }
    ]
  },
  {
    path: '/pve/vm/detail',
    component: Layout,
    hidden: true,
    children: [
      {
        path: ':id',
        name: 'PVEVirtualMachineDetail',
        component: () => import('@/views/pve/vm/detail.vue'),
        meta: {
          title: '虚拟机详情',
          activeMenu: '/pve/vm'
        }
      }
    ]
  },
]

// 动态路由（从后端菜单生成）
let dynamicRoutes = []
const catchAllRouteName = 'catchAll'
const rootRouteName = 'rootRedirect'

const buildRouter = () => createRouter({
  history: createWebHashHistory(),
  routes: [...constantRoutes, ...dynamicRoutes]
})

const router = buildRouter()

/**
 * 动态添加路由
 * @param {Array} menuTree - 后端返回的菜单树
 */
export function addDynamicRoutes(menuTree) {
  // 移除旧的路由
  dynamicRoutes.forEach(route => {
    try {
      if (route.name && router.hasRoute && router.hasRoute(route.name)) {
        router.removeRoute(route.name)
      }
    } catch (e) {
      // 忽略
    }
  })

  // 移除 catchAll 路由（如果存在）
  try {
    if (router.hasRoute && router.hasRoute(catchAllRouteName)) {
      router.removeRoute(catchAllRouteName)
    }
  } catch (e) {
    // 忽略
  }

  // 生成新路由
  dynamicRoutes = menuTreeToRoutes(menuTree)

  console.log('生成的动态路由:', dynamicRoutes)

  // 添加新路由
  dynamicRoutes.forEach(route => {
    try {
      router.addRoute(route)
    } catch (e) {
      console.error('添加路由失败:', route, e)
    }
  })

  // 添加根路径重定向（如果存在第一个菜单）
  if (dynamicRoutes.length > 0) {
    const firstRoute = dynamicRoutes[0]
    // 如果第一个路由有 redirect，使用它的 redirect
    // 否则使用第一个路由的路径
    const rootRedirect = firstRoute.redirect || firstRoute.path

    // 移除旧的根路径路由（使用命名路由移除）
    try {
      if (router.hasRoute && router.hasRoute(rootRouteName)) {
        router.removeRoute(rootRouteName)
      }
    } catch (e) {
      // 忽略
    }

    // 添加新的根路径重定向
    router.addRoute({
      name: rootRouteName,
      path: '/',
      redirect: rootRedirect,
      hidden: true
    })
  }

  // 添加 catchAll 路由（必须在最后）
  try {
    if (router.hasRoute && router.hasRoute(catchAllRouteName)) {
      router.removeRoute(catchAllRouteName)
    }
  } catch (e) {}
  router.addRoute({
    name: catchAllRouteName,
    path: '/:catchAll(.*)',
    redirect: '/404',
    hidden: true
  })
}

export default router
