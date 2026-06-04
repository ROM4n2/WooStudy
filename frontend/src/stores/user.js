/** 用户状态——管理设置 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSettings as fetchSettings, updateSettings as saveSettings } from '../api/settings'

export const useUserStore = defineStore('user', () => {
  const sessionId = ref('')       // 由 ChatView 在加载时从 chat store 同步
  const deepMode = ref(false)    // 深度优先模式
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
