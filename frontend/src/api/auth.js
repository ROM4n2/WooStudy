/** 认证相关 API */
import request from './request'

export function register(username, password, mimo_api_key, deepseek_api_key) {
  return request.post('/auth/register', { username, password, mimo_api_key, deepseek_api_key })
}

export function login(username, password) {
  return request.post('/auth/login', { username, password })
}

export function getMe() {
  return request.get('/auth/me')
}

export function updateApiKeys(mimo_api_key, deepseek_api_key) {
  return request.put('/auth/keys', { mimo_api_key, deepseek_api_key })
}
