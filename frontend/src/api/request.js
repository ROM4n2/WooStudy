/** axios 实例——统一认证和基础 URL */
import axios from 'axios'

// 开发环境用 Vite 本地代理，生产环境优先读 env 变量，兜底指向 Railway
const API_BASE = import.meta.env.DEV
  ? '/api'
  : (import.meta.env.VITE_API_BASE || 'https://woostudy-production.up.railway.app')

const request = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
})

// 请求拦截器：自动附加 JWT token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('woostudy_token')
  // 仍然保留 session_id 用于历史数据兼容
  const sessionId = localStorage.getItem('woostudy_session_id')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  if (sessionId) {
    config.params = {
      ...config.params,
      session_id: sessionId,
    }
  }
  return config
})

// 响应拦截器：统一错误处理
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    console.error('[API Error]', msg)
    return Promise.reject(new Error(msg))
  },
)

export default request
