/** 用户会话状态——管理 session_id 和设置 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSettings as fetchSettings, updateSettings as saveSettings } from '../api/settings'

// 生成唯一 session_id（浏览器本地存储以跨页面持久化）
function generateSessionId() {
  const stored = localStorage.getItem('wuzhixue_session_id')
  if (stored) return stored
  const id = 'session_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8)
  localStorage.setItem('wuzhixue_session_id', id)
  return id
}

export const useUserStore = defineStore('user', () => {
  const sessionId = ref(generateSessionId())
  const deepMode = ref(false)  // 深度优先模式
  const loading = ref(false)

  async function loadSettings() {
    try {
      const res = await fetchSettings()
      deepMode.value = res.settings?.deep_mode ?? false
    } catch {
      // 静默失败，使用默认值
    }
  }

  async function toggleDeepMode() {
    deepMode.value = !deepMode.value
    try {
      await saveSettings({ deep_mode: deepMode.value })
    } catch {
      // 回滚
      deepMode.value = !deepMode.value
    }
  }

  return { sessionId, deepMode, loading, loadSettings, toggleDeepMode }
})
