/**
 * 组件加载器：用于动态加载页面组件
 * 解决 Vite 动态 import 路径解析问题
 */

// 组件映射表（显式导入，确保路径正确）
const componentMap = {
  'system/user/index': () => import('@/views/system/user/index.vue'),
  'system/role/index': () => import('@/views/system/role/index.vue'),
  'system/menu/index': () => import('@/views/system/menu/index.vue'),
  'system/permission/index': () => import('@/views/system/permission/index.vue'),
  'system/organization/index': () => import('@/views/system/organization/index.vue'),
  'system/codegen/index': () => import('@/views/system/codegen/index.vue'),
  'curdexample/index': () => import('@/views/curdexample/index.vue'),
  // 自动添加其他路径
}

/**
 * 动态加载组件
 * @param {string} componentPath - 组件路径，如 'system/user/index'
 * @returns {Promise} 组件导入 Promise
 */
export function loadComponent(componentPath) {
  // 先从映射表查找
  if (componentMap[componentPath]) {
    return componentMap[componentPath]()
  }
  
  // 如果映射表中没有，尝试动态导入
  const fullPath = componentPath.startsWith('@/') 
    ? componentPath 
    : `@/views/${componentPath}`
  
  return import(/* @vite-ignore */ fullPath).catch((err) => {
    console.error('加载组件失败:', fullPath, err)
    // 返回默认菜单页面
    return import('@/views/menu-page/index.vue')
  })
}

