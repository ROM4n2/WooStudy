import request from './request'

export function getReport(forceRefresh = false) {
  return request.get('/analysis/report', { params: { force_refresh: forceRefresh } })
}

export function getJourney() {
  return request.get('/analysis/journey')
}
