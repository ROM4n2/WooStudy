/** 知识图谱 API */
import request from './request'

export function getKnowledgeGraph() {
  return request.get('/knowledge/graph')
}
