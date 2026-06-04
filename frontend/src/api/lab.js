import request from './request'

export function getLabList() {
  return request.get('/lab/list')
}

export function recordSession(labName, labTitle, durationSeconds) {
  return request.post('/lab/session', {
    lab_name: labName,
    lab_title: labTitle,
    duration_seconds: durationSeconds,
  })
}
