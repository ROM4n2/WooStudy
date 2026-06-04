import request from './request'

export function getSettings() {
  return request.get('/settings')
}

export function updateSettings(settings) {
  return request.put('/settings', { settings })
}
