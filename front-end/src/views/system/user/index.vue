<template>
  <div class="user-management">
    <a-card>
      <template #title>
        <a-typography-title :heading="4">用户管理</a-typography-title>
      </template>

      <!-- 工具栏 -->
      <div class="toolbar">
        <a-space>
          <a-input-search
            v-model="searchText"
            placeholder="搜索用户名、邮箱或姓名"
            style="width: 300px"
            @search="handleSearch"
            @clear="handleSearch"
            allow-clear
          />
          <a-button type="primary" @click="handleCreate">
            <template #icon>
              <icon-plus />
            </template>
            新增用户
          </a-button>
        </a-space>
      </div>

      <!-- 表格 -->
      <a-table
        :columns="columns"
        :data="tableData"
        :loading="loading"
        :pagination="pagination"
        @page-change="handlePageChange"
        @page-size-change="handlePageSizeChange"
        :bordered="false"
        :hoverable="true"
        style="margin-top: 16px"
      >
        <template #is_active="{ record }">
          <a-tag :color="record.is_active ? 'green' : 'red'">
            {{ record.is_active ? '启用' : '禁用' }}
          </a-tag>
        </template>

        <template #is_staff="{ record }">
          <a-tag :color="record.is_staff ? 'blue' : 'gray'">
            {{ record.is_staff ? '是' : '否' }}
          </a-tag>
        </template>

        <template #is_superuser="{ record }">
          <a-tag :color="record.is_superuser ? 'red' : 'gray'">
            {{ record.is_superuser ? '是' : '否' }}
          </a-tag>
        </template>

        <template #date_joined="{ record }">
          {{ formatDate(record.date_joined) }}
        </template>

        <template #last_login="{ record }">
          {{ record.last_login ? formatDate(record.last_login) : '-' }}
        </template>

        <template #actions="{ record }">
          <a-space :size="8">
            <a-button type="text" size="small" @click="handleEdit(record)">编辑</a-button>
            <a-button type="text" size="small" @click="handleManageRolesOrgs(record)">角色/组织</a-button>
            <a-button type="text" size="small" status="danger" @click="handleDelete(record)">删除</a-button>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <!-- 表单对话框 -->
    <a-modal
      v-model:visible="formVisible"
      :title="formTitle"
      @before-ok="handleSubmit"
      @cancel="handleCancel"
      :width="600"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="getFormRules()"
        layout="vertical"
      >
        <a-form-item field="username" label="用户名">
          <a-input v-model="formData.username" placeholder="请输入用户名" />
        </a-form-item>

        <a-form-item field="email" label="邮箱">
          <a-input v-model="formData.email" placeholder="请输入邮箱" type="email" />
        </a-form-item>

        <a-form-item v-if="!formData.id" field="password" label="密码">
          <a-input-password v-model="formData.password" placeholder="请输入密码（至少6位）" />
        </a-form-item>

        <a-form-item v-if="formData.id" field="password" label="密码（留空不修改）">
          <a-input-password v-model="formData.password" placeholder="留空则不修改密码" />
        </a-form-item>

        <a-form-item field="first_name" label="名">
          <a-input v-model="formData.first_name" placeholder="请输入名" />
        </a-form-item>

        <a-form-item field="last_name" label="姓">
          <a-input v-model="formData.last_name" placeholder="请输入姓" />
        </a-form-item>

        <a-form-item field="is_active" label="是否启用">
          <a-switch v-model="formData.is_active" />
        </a-form-item>

        <a-form-item field="is_staff" label="是否员工">
          <a-switch v-model="formData.is_staff" />
        </a-form-item>

        <a-form-item field="is_superuser" label="是否超级管理员">
          <a-switch v-model="formData.is_superuser" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 角色和组织管理对话框 -->
    <a-modal
      v-model:visible="rolesOrgsVisible"
      title="管理角色和组织"
      @before-ok="handleSaveRolesOrgs"
      @cancel="handleCancelRolesOrgs"
      :width="700"
    >
      <a-form layout="vertical">
        <a-form-item label="用户名">
          <a-typography-text>{{ currentUser.username || '未设置' }}</a-typography-text>
        </a-form-item>

        <a-form-item label="角色">
          <a-select
            v-model="selectedRoles"
            placeholder="请选择角色"
            multiple
            :loading="rolesLoading"
            allow-search
          >
            <a-option
              v-for="role in roleList"
              :key="role.id"
              :value="role.id"
            >
              {{ role.name }} ({{ role.code }})
            </a-option>
          </a-select>
        </a-form-item>

        <a-form-item label="组织">
          <a-select
            v-model="selectedOrganizations"
            placeholder="请选择组织"
            multiple
            :loading="organizationsLoading"
            allow-search
            @change="handleOrganizationsChange"
          >
            <a-option
              v-for="org in organizationList"
              :key="org.id"
              :value="org.id"
            >
              {{ org.name }}
            </a-option>
          </a-select>
        </a-form-item>

        <a-form-item label="主组织" v-if="selectedOrganizations.length > 0">
          <a-select
            v-model="primaryOrganization"
            placeholder="请选择主组织"
            allow-clear
          >
            <a-option
              v-for="orgId in selectedOrganizations"
              :key="orgId"
              :value="orgId"
            >
              {{ getOrganizationName(orgId) }}
            </a-option>
          </a-select>
          <template #extra>
            <div style="color: #86909c; font-size: 12px; margin-top: 4px;">
              提示：选择了组织时，必须选择一个主组织
            </div>
          </template>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { IconPlus } from '@arco-design/web-vue/es/icon'
import {
  getUserList,
  getUserDetail,
  createUser,
  updateUser,
  deleteUser
} from '@/api/user-management'
import {
  getUserRoleList,
  createUserRole,
  deleteUserRole
} from '@/api/user-role'
import {
  getUserOrganizationList,
  createUserOrganization,
  deleteUserOrganization,
  updateUserOrganization
} from '@/api/user-organization'
import { getRoleList } from '@/api/role'
import { getOrganizationList } from '@/api/organization'

const columns = [
  { title: 'ID', dataIndex: 'id', width: 80 },
  { title: '用户名', dataIndex: 'username' },
  { title: '邮箱', dataIndex: 'email' },
  { title: '姓名', dataIndex: 'first_name', render: ({ record }) => `${record.first_name || ''} ${record.last_name || ''}`.trim() || '-' },
  { title: '启用', dataIndex: 'is_active', slotName: 'is_active', width: 100 },
  { title: '员工', dataIndex: 'is_staff', slotName: 'is_staff', width: 100 },
  { title: '超级管理员', dataIndex: 'is_superuser', slotName: 'is_superuser', width: 120 },
  { title: '注册时间', dataIndex: 'date_joined', slotName: 'date_joined', width: 180 },
  { title: '最后登录', dataIndex: 'last_login', slotName: 'last_login', width: 180 },
  { title: '操作', slotName: 'actions', width: 220, fixed: 'right' }
]

const searchText = ref('')
const loading = ref(false)
const tableData = ref([])
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showTotal: true,
  showPageSize: true
})

const formVisible = ref(false)
const formTitle = ref('新增用户')
const formRef = ref()
const formData = reactive({
  id: null,
  username: '',
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  is_active: true,
  is_staff: false,
  is_superuser: false
})

// 角色和组织管理相关
const rolesOrgsVisible = ref(false)
const currentUser = reactive({
  id: null,
  username: '',
  email: ''
})
const roleList = ref([])
const organizationList = ref([])
const selectedRoles = ref([])
const selectedOrganizations = ref([])
const primaryOrganization = ref(null)
const rolesLoading = ref(false)
const organizationsLoading = ref(false)

// 动态表单验证规则
const getFormRules = () => {
  const rules = {
    username: [{ required: true, message: '请输入用户名' }],
    email: [{ required: true, type: 'email', message: '请输入有效的邮箱地址' }]
  }
  
  // 新增时密码必填，编辑时可选
  if (!formData.id) {
    rules.password = [
      { required: true, message: '请输入密码' },
      { min: 6, message: '密码至少6位' }
    ]
  } else {
    rules.password = [
      {
        validator: (value, cb) => {
          // 编辑时，如果填写了密码，则验证长度
          if (value && value.length < 6) {
            cb('密码至少6位')
          } else {
            cb()
          }
        }
      }
    ]
  }
  
  return rules
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 获取列表数据
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize
    }
    if (searchText.value) {
      params.search = searchText.value
    }
    const res = await getUserList(params)
    tableData.value = res.results || res.data || []
    pagination.total = res.count || res.total || 0
  } catch (e) {
    Message.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.current = 1
  fetchData()
}

// 分页
const handlePageChange = (page) => {
  pagination.current = page
  fetchData()
}

const handlePageSizeChange = (pageSize) => {
  pagination.pageSize = pageSize
  pagination.current = 1
  fetchData()
}

// 新增
const handleCreate = () => {
  formTitle.value = '新增用户'
  Object.assign(formData, {
    id: null,
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    is_active: true,
    is_staff: false,
    is_superuser: false
  })
  formVisible.value = true
}

// 编辑
const handleEdit = async (record) => {
  formTitle.value = '编辑用户'
  try {
    const res = await getUserDetail(record.id)
    Object.assign(formData, {
      id: res.id,
      username: res.username,
      email: res.email || '',
      password: '', // 编辑时不显示密码
      first_name: res.first_name || '',
      last_name: res.last_name || '',
      is_active: res.is_active !== undefined ? res.is_active : true,
      is_staff: res.is_staff || false,
      is_superuser: res.is_superuser || false
    })
    formVisible.value = true
  } catch (e) {
    Message.error('获取详情失败')
  }
}

// 删除
const handleDelete = (record) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除用户"${record.username}"吗？`,
    onOk: async () => {
      try {
        await deleteUser(record.id)
        Message.success('删除成功')
        fetchData()
      } catch (e) {
        Message.error('删除失败')
      }
    }
  })
}

// 提交表单（使用 before-ok，需要返回 Promise 或 false 来阻止关闭）
const handleSubmit = async () => {
  console.log('handleSubmit 被调用', formData)
  
  // Arco Design 的表单验证：验证失败会抛出错误，成功返回 undefined
  try {
    await formRef.value?.validate()
    console.log('表单验证通过')
  } catch (error) {
    console.log('表单验证失败:', error)
    return false // 验证失败，阻止关闭
  }

  try {
    const data = {
      username: formData.username,
      email: formData.email,
      first_name: formData.first_name || '',
      last_name: formData.last_name || '',
      is_active: formData.is_active,
      is_staff: formData.is_staff,
      is_superuser: formData.is_superuser
    }

    if (formData.id) {
      // 编辑：只有提供了密码才发送
      console.log('编辑用户，ID:', formData.id)
      if (formData.password && formData.password.trim()) {
        data.password = formData.password
      }
      console.log('调用 updateUser API，数据:', data)
      await updateUser(formData.id, data)
      console.log('updateUser 成功')
      Message.success('更新成功')
    } else {
      // 新增：密码必填
      console.log('新增用户，数据:', data)
      if (!formData.password || formData.password.trim().length < 6) {
        Message.error('密码至少6位')
        return false // 阻止关闭
      }
      data.password = formData.password
      console.log('调用 createUser API，数据:', data)
      await createUser(data)
      console.log('createUser 成功')
      Message.success('创建成功')
    }

    formVisible.value = false
    fetchData()
    return true // 允许关闭
  } catch (e) {
    console.error('提交失败:', e)
    const errorMsg = e.response?.data?.detail || e.response?.data?.message || (formData.id ? '更新失败' : '创建失败')
    Message.error(errorMsg)
    return false // 错误时阻止关闭
  }
}

// 取消
const handleCancel = () => {
  formVisible.value = false
}

// 获取组织名称
const getOrganizationName = (orgId) => {
  const org = organizationList.value.find(o => o.id === orgId)
  return org ? org.name : ''
}

// 组织选择变化时的处理
const handleOrganizationsChange = (value) => {
  // 如果清空了所有组织，也清除主组织
  if (!value || value.length === 0) {
    primaryOrganization.value = null
  } else if (primaryOrganization.value && !value.includes(primaryOrganization.value)) {
    // 如果主组织不在选中列表中，清除主组织
    primaryOrganization.value = null
  }
}

// 加载角色列表
const loadRoleList = async () => {
  rolesLoading.value = true
  try {
    const res = await getRoleList()
    roleList.value = res.results || res.data || []
  } catch (e) {
    Message.error('加载角色列表失败')
  } finally {
    rolesLoading.value = false
  }
}

// 加载组织列表
const loadOrganizationList = async () => {
  organizationsLoading.value = true
  try {
    const res = await getOrganizationList()
    organizationList.value = res.results || res.data || []
  } catch (e) {
    Message.error('加载组织列表失败')
  } finally {
    organizationsLoading.value = false
  }
}

// 加载用户的角色和组织
const loadUserRolesOrgs = async (userId) => {
  try {
    // 加载用户角色
    const rolesRes = await getUserRoleList({ user: userId })
    const userRoles = rolesRes.results || rolesRes.data || []
    selectedRoles.value = userRoles.map(ur => ur.role)

    // 加载用户组织
    const orgsRes = await getUserOrganizationList({ user: userId })
    const userOrgs = orgsRes.results || orgsRes.data || []
    selectedOrganizations.value = userOrgs.map(uo => uo.organization)
    
    // 找到主组织
    const primaryOrg = userOrgs.find(uo => uo.is_primary)
    if (primaryOrg) {
      primaryOrganization.value = primaryOrg.organization
    } else {
      primaryOrganization.value = null
    }
  } catch (e) {
    Message.error('加载用户角色和组织失败')
  }
}

// 管理角色和组织
const handleManageRolesOrgs = async (record) => {
  console.log('handleManageRolesOrgs - record:', record)
  
  // 更新 currentUser 对象（使用 reactive 对象，直接赋值属性）
  currentUser.id = record.id
  currentUser.username = record.username || ''
  currentUser.email = record.email || ''
  
  console.log('currentUser:', currentUser)
  console.log('currentUser.username:', currentUser.username)
  
  // 先显示对话框
  rolesOrgsVisible.value = true
  
  // 然后加载数据
  await Promise.all([
    loadRoleList(),
    loadOrganizationList(),
    loadUserRolesOrgs(record.id)
  ])
}

// 保存角色和组织
const handleSaveRolesOrgs = async () => {
  if (!currentUser.id) return false

  // 验证主组织：如果选择了组织，必须选择主组织
  if (selectedOrganizations.value.length > 0 && !primaryOrganization.value) {
    Message.error('选择了组织时，必须选择一个主组织')
    return false
  }

  try {
    const userId = currentUser.id

    // 1. 处理角色
    // 获取当前用户的角色
    const currentRolesRes = await getUserRoleList({ user: userId })
    const currentUserRoles = currentRolesRes.results || currentRolesRes.data || []
    const currentRoleIds = new Set(currentUserRoles.map(ur => ur.role))
    const newRoleIds = new Set(selectedRoles.value)

    // 删除不再需要的角色
    for (const userRole of currentUserRoles) {
      if (!newRoleIds.has(userRole.role)) {
        await deleteUserRole(userRole.id)
      }
    }

    // 添加新角色
    for (const roleId of selectedRoles.value) {
      if (!currentRoleIds.has(roleId)) {
        await createUserRole({
          user: userId,
          role: roleId
        })
      }
    }

    // 2. 处理组织
    // 获取当前用户的组织
    const currentOrgsRes = await getUserOrganizationList({ user: userId })
    const currentUserOrgs = currentOrgsRes.results || currentOrgsRes.data || []
    const currentOrgIds = new Set(currentUserOrgs.map(uo => uo.organization))
    const newOrgIds = new Set(selectedOrganizations.value)

    // 删除不再需要的组织
    for (const userOrg of currentUserOrgs) {
      if (!newOrgIds.has(userOrg.organization)) {
        await deleteUserOrganization(userOrg.id)
      }
    }

    // 添加或更新组织
    for (const orgId of selectedOrganizations.value) {
      const existingUserOrg = currentUserOrgs.find(uo => uo.organization === orgId)
      
      if (existingUserOrg) {
        // 更新主组织标记
        if (existingUserOrg.is_primary !== (orgId === primaryOrganization.value)) {
          await updateUserOrganization(existingUserOrg.id, {
            user: userId,
            organization: orgId,
            is_primary: orgId === primaryOrganization.value
          })
        }
      } else {
        // 创建新组织关联
        await createUserOrganization({
          user: userId,
          organization: orgId,
          is_primary: orgId === primaryOrganization.value
        })
      }
    }

    // 确保只有一个主组织
    if (primaryOrganization.value) {
      const allUserOrgsRes = await getUserOrganizationList({ user: userId })
      const allUserOrgs = allUserOrgsRes.results || allUserOrgsRes.data || []
      
      for (const userOrg of allUserOrgs) {
        if (userOrg.organization !== primaryOrganization.value && userOrg.is_primary) {
          await updateUserOrganization(userOrg.id, {
            user: userId,
            organization: userOrg.organization,
            is_primary: false
          })
        }
      }
    }

    Message.success('保存成功')
    rolesOrgsVisible.value = false
    return true
  } catch (e) {
    const errorMsg = e.response?.data?.detail || e.response?.data?.message || '保存失败'
    Message.error(errorMsg)
    return false
  }
}

// 取消角色和组织管理
const handleCancelRolesOrgs = () => {
  rolesOrgsVisible.value = false
  currentUser.id = null
  currentUser.username = ''
  currentUser.email = ''
  selectedRoles.value = []
  selectedOrganizations.value = []
  primaryOrganization.value = null
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.toolbar {
  margin-bottom: 16px;
}
</style>
