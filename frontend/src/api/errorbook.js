import request from './request'

export function getErrorLogs(params = {}) {
  return request.get('/errorbook', { params })
}

export function markReviewed(errorId, reviewed = true) {
  return request.put(`/errorbook/${errorId}/review`, { reviewed })
}

export function generateVariant(errorId) {
  return request.post(`/errorbook/${errorId}/variant`)
}
