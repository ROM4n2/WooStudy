import { createRouter, createWebHistory } from 'vue-router'
import { STORAGE_KEYS } from '../constants/keys'
import ChatView from '../views/ChatView.vue'

const routes = [
  {
    path: '/',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
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
  {
    path: '/journey',
    name: 'journey',
    component: () => import('../views/JourneyView.vue'),
  },
  {
    path: '/knowledge',
    name: 'knowledge',
    component: () => import('../views/KnowledgeGraphView.vue'),
  },
  {
    path: '/contribute',
    name: 'contribute',
    component: () => import('../views/ContributorView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 导航守卫：未登录则跳回首页
router.beforeEach((to, from, next) => {
  if (to.path === '/') {
    next()
    return
  }
  const token = localStorage.getItem(STORAGE_KEYS.TOKEN)
  if (token) {
    next()
  } else {
    next('/')
  }
})

export default router
