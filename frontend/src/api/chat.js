import request from './request'
import { STORAGE_KEYS } from '../constants/keys'
import { useUserStore } from '../stores/user'

// ── Session 管理 ──

export function getSessions() {
  // 匿名用户：从 localStorage 取所有已知 session_id
  const ids = localStorage.getItem(STORAGE_KEYS.SESSION_IDS)
  const params = ids ? { session_ids: ids } : {}
  return request.get('/chat/sessions', { params })
}

export function createSession(sessionId) {
  return request.post('/chat/sessions', { session_id: sessionId })
}

export function deleteSession(sessionId) {
  return request.delete(`/chat/sessions/${sessionId}`)
}

// ── 对话 ──

export function sendMessage(content, deepMode = false, followUp = false) {
  return request.post('/chat/send', { content }, { params: { deep_mode: deepMode, follow_up: followUp } })
}

export function uploadImage(content, file, deepMode = false) {
  const userStore = useUserStore()
  const form = new FormData()
  form.append('session_id', userStore.sessionId)
  form.append('content', content)
  form.append('image', file)
  form.append('deep_mode', String(deepMode))
  return request.post('/chat/upload', form)
}

export function getHistory(limit = 50) {
  return request.get('/chat/history', { params: { limit } })
}

export function optimizePrompt(text) {
  return request.post('/chat/optimize', { text })
}
