import { login, logout, getUserInfo } from "@/api/user"

const getDefaultState = () => {
  return {
    id: null,
    username: '',
    email: '',
    is_superuser: false,
    roles: [],
    permissions: [],
    primary_organization: null,
  }
}

const state = getDefaultState()

const actions = {
  /**
   * 登录
   * @param {Object} loginForm - 登录表单 { username, password }
   * @returns {Promise<boolean>} 登录是否成功
   */
  async login({ commit }, loginForm) {
    try {
      console.log('[store.user] login payload:', loginForm)
      const res = await login(loginForm)
      console.log('[store.user] login response:', res)
      // 后端返回：{ id, username, roles, permissions }
      commit('SET_USER_INFO', {
        id: res.id,
        username: res.username,
        roles: res.roles || [],
        permissions: res.permissions || [],
      })
      return true
    } catch (e) {
      console.error('[store.user] 登录失败:', e)
      return false
    }
  },

  /**
   * 获取用户信息
   * @returns {Promise<boolean>} 获取是否成功
   */
  async getUserInfo({ commit }) {
    try {
      console.log('[store.user] fetching user info...')
      const res = await getUserInfo()
      console.log('[store.user] user info response:', res)
      commit('SET_USER_INFO', {
        id: res.id,
        username: res.username,
        email: res.email || '',
        is_superuser: res.is_superuser || false,
        roles: res.roles || [],
        permissions: res.permissions || [],
        primary_organization: res.primary_organization || null,
      })
      return true
    } catch (e) {
      console.error('[store.user] 获取用户信息失败:', e)
      return false
    }
  },

  /**
   * 退出登录
   */
  async logout({ commit }) {
    try {
      await logout()
    } catch (ignore) {
      // 即使退出失败也清除本地状态
    }

    commit('RESET_STATE')
  }
}

const mutations = {
  RESET_STATE: (state) => {
    Object.assign(state, getDefaultState())
  },
  SET_USER_INFO: (state, userInfo) => {
    Object.assign(state, userInfo)
  },
}

const getters = {
  // 检查是否有某个权限
  hasPermission: (state) => (permissionCode) => {
    if (state.is_superuser) return true
    return state.permissions.includes(permissionCode)
  },
  // 检查是否有某个角色
  hasRole: (state) => (roleCode) => {
    if (state.is_superuser) return true
    return state.roles.some(role => 
      typeof role === 'string' ? role === roleCode : role.code === roleCode
    )
  },
}

export default {
  namespaced: true,
  state,
  actions,
  mutations,
  getters
}
