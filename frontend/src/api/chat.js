import request from './request'
import { useUserStore } from '../stores/user'

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
