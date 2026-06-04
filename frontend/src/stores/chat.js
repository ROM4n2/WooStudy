/** 对话状态管理——多 session 列表、切换、新建、删除 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { STORAGE_KEYS } from '../constants/keys'
import { getSessions, createSession, deleteSession } from '../api/chat'

// 生成唯一 session_id
function generateSessionId() {
  const id = 'session_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8)
  return id
}

// 管理 localStorage 中的 session_id 列表
function loadSessionIds() {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.SESSION_IDS)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveSessionIds(ids) {
  localStorage.setItem(STORAGE_KEYS.SESSION_IDS, JSON.stringify(ids))
}

// 迁移旧的单 session ID
function migrateOldSession() {
  const oldId = localStorage.getItem('woostudy_session_id')
  if (!oldId) return null
  const ids = loadSessionIds()
  if (!ids.includes(oldId)) {
    ids.unshift(oldId)
    saveSessionIds(ids)
  }
  return oldId
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref([])         // 按 updated_at 降序的 session 列表
  const currentId = ref('')        // 当前选中的 session_id
  const loaded = ref(false)        // 是否已从后端加载
  const loading = ref(false)       // 加载中

  // 日期分组计算属性
  const groupedSessions = computed(() => {
    const groups = {}
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    const weekStart = new Date(today)
    weekStart.setDate(weekStart.getDate() - weekStart.getDay())

    const todayStr = today.toDateString()
    const yesterdayStr = yesterday.toDateString()

    for (const s of sessions.value) {
      const d = new Date(s.updated_at || s.created_at)
      const dStr = d.toDateString()
      let groupKey
      if (dStr === todayStr) groupKey = '今天'
      else if (dStr === yesterdayStr) groupKey = '昨天'
      else if (d >= weekStart) groupKey = '本周'
      else groupKey = '更早'

      if (!groups[groupKey]) groups[groupKey] = []
      groups[groupKey].push(s)
    }
    return groups
  })

  async function loadSessions() {
    if (loading.value) return
    loading.value = true
    try {
      // 迁移旧 session
      const oldId = migrateOldSession()

      const res = await getSessions()
      // 扁平化分组
      const all = []
      for (const group of Object.values(res.groups || {})) {
        all.push(...group)
      }
      sessions.value = all

      // 确定当前 session
      if (currentId.value && all.some(s => s.session_id === currentId.value)) {
        // 已选中有效 session，保持不变
      } else if (oldId && all.some(s => s.session_id === oldId)) {
        currentId.value = oldId
      } else if (all.length > 0) {
        currentId.value = all[0].session_id
      } else {
        // 一个 session 都没有，新建一个
        await createNewSession()
      }

      syncSessionId(currentId.value)
      loaded.value = true
    } catch {
      // 后端不可用时用本地兜底
      if (!currentId.value) {
        currentId.value = migrateOldSession() || generateSessionId()
      }
      syncSessionId(currentId.value)
      loaded.value = true
    } finally {
      loading.value = false
    }
  }

  // 同步当前 session 到 localStorage（供 request.js 拦截器读取）
  function syncSessionId(id) {
    if (id) localStorage.setItem('woostudy_session_id', id)
  }

  async function createNewSession() {
    const id = generateSessionId()
    try {
      await createSession(id)
    } catch {
      // 静默
    }
    // 无论后端成功与否，本地都记录
    const ids = loadSessionIds()
    ids.unshift(id)
    saveSessionIds(ids)

    sessions.value.unshift({ session_id: id, title: '新对话', created_at: new Date().toISOString(), updated_at: new Date().toISOString() })
    currentId.value = id
    syncSessionId(id)
    return id
  }

  async function removeSession(sessionId) {
    try {
      await deleteSession(sessionId)
    } catch {
      // 静默
    }
    // 本地移除
    sessions.value = sessions.value.filter(s => s.session_id !== sessionId)
    const ids = loadSessionIds().filter(id => id !== sessionId)
    saveSessionIds(ids)

    // 如果删除的是当前 session，切换到第一个
    if (currentId.value === sessionId) {
      currentId.value = sessions.value.length > 0 ? sessions.value[0].session_id : ''
    }
  }

  function switchSession(sessionId) {
    if (sessionId === currentId.value) return
    currentId.value = sessionId
    syncSessionId(sessionId)
  }

  function updateSessionTitle(sessionId, title) {
    const s = sessions.value.find(s => s.session_id === sessionId)
    if (s) s.title = title
  }

  return {
    sessions,
    currentId,
    loaded,
    loading,
    groupedSessions,
    loadSessions,
    createNewSession,
    removeSession,
    switchSession,
    updateSessionTitle,
  }
})
