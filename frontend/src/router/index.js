import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'

const routes = [
  {
    path: '/',
    name: 'gate',
    component: () => import('../views/AccessGate.vue'),
  },
  {
    path: '/chat',
    name: 'chat',
    component: ChatView,
  },
  {
    path: '/errorbook',
    name: 'errorbook',
    component: () => import('../views/ErrorBookView.vue'),
  },
  {
    path: '/practice',
    name: 'practice',
    component: () => import('../views/PracticeView.vue'),
  },
  {
    path: '/lab',
    name: 'lab',
    component: () => import('../views/LabView.vue'),
  },
  {
    path: '/analysis',
    name: 'analysis',
    component: () => import('../views/AnalysisView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 导航守卫：未通过密码门禁则跳回首页
router.beforeEach((to, from, next) => {
  // 首页（密码门禁）不需要验证
  if (to.path === '/') {
    next()
    return
  }
  // 检查是否已通过密码验证
  const gatePassed = localStorage.getItem('woostudy_gate')
  if (gatePassed === 'true') {
    next()
  } else {
    next('/')
  }
})

export default router
