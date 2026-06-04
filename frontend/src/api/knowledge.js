/** 知识图谱 API */
import request from './request'

// ── 图谱读取 ──

export function getKnowledgeGraph() {
  return request.get('/knowledge/graph')
}

// ── 用户标记 ──

export function addMarker(nodeId, markerType, note = '') {
  return request.post('/knowledge/markers', { node_id: nodeId, marker_type: markerType, note })
}

export function removeMarker(nodeId, markerType) {
  return request.delete('/knowledge/markers', { params: { node_id: nodeId, marker_type: markerType } })
}

export function getMarkers() {
  return request.get('/knowledge/markers')
}

// ── 用户贡献 ──

export function submitContribution(data) {
  return request.post('/knowledge/contributions', data)
}

/** 管理员：获取待审核列表 */
export function getPendingContributions() {
  return request.get('/knowledge/pending')
}

/** 管理员：批准 */
export function approveContribution(nodeId) {
  return request.put(`/knowledge/pending/${nodeId}/approve`)
}

/** 管理员：拒绝 */
export function rejectContribution(nodeId) {
  return request.put(`/knowledge/pending/${nodeId}/reject`)
}
