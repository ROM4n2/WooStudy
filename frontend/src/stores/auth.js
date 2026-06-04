/** 用户认证状态管理 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import router from '../router'
import * as authApi from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('woostudy_token') || '')
  const user = ref(null)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!token.value && !!user.value)

  function setToken(newToken) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('woostudy_token', newToken)
    } else {
      localStorage.removeItem('woostudy_token')
    }
  }

  async function login(username, password) {
    loading.value = true
    try {
      const res = await authApi.login(username, password)
      setToken(res.token)
      user.value = { id: res.user_id, username: res.username, has_api_keys: res.has_api_keys }
      return res
    } finally {
      loading.value = false
    }
  }

  async function register(username, password, mimoKey, deepseekKey) {
    loading.value = true
    try {
      const res = await authApi.register(username, password, mimoKey, deepseekKey)
      setToken(res.token)
      user.value = { id: res.user_id, username: res.username, has_api_keys: true }
      return res
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!token.value) return null
    try {
      const res = await authApi.getMe()
      user.value = {
        id: res.user_id,
        username: res.username,
        has_api_keys: res.has_api_keys,
      }
      return res
    } catch {
      logout()
      return null
    }
  }

  async function updateApiKeys(mimoKey, deepseekKey) {
    const res = await authApi.updateApiKeys(mimoKey, deepseekKey)
    if (user.value) {
      user.value.has_api_keys = res.has_api_keys
    }
    return res
  }

  function logout() {
    setToken('')
    user.value = null
    localStorage.removeItem('woostudy_gate')
    router.push('/')
  }

  return { token, user, loading, isLoggedIn, login, register, fetchMe, updateApiKeys, logout }
})
