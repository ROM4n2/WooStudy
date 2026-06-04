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
