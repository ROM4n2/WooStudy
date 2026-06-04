import request from './request'

export function getQuestions(params = {}) {
  return request.get('/practice', { params })
}

export function submitAnswer(questionId, answer) {
  return request.post('/practice/submit', { question_id: questionId, answer })
}
