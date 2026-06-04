/** axios 实例——统一处理 session_id 和基础 URL */

import axios from 'axios'
import { useUserStore } from '../stores/user'

// 生产环境：VITE_API_BASE 指向 Railway 后端地址（如 https://your-app.railway.app）
// 开发环境：Vite proxy 转发 /api → localhost:8000
const API_BASE = import.meta.env.VITE_API_BASE || '/api'

const request = axios.create({
  baseURL: API_BASE,
  timeout: 60000,  // AI 响应可能较慢，超时设为 60s
})

// 请求拦截器：自动附加 session_id
request.interceptors.request.use((config) => {
  const userStore = useUserStore()
  config.params = {
    ...config.params,
    session_id: userStore.sessionId,
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
