<template>
  <div class="gate">
    <div class="gate-card">
      <div class="gate-brand">
        <span class="gate-icon">⚛️</span>
        <h1 class="gate-title">物知学</h1>
        <p class="gate-subtitle">高中物理 AI 助学</p>
      </div>

      <div v-if="!authed" class="gate-form">
        <p class="gate-hint">请输入访问密码</p>
        <div class="input-group">
          <input
            ref="passwordInput"
            v-model="password"
            type="password"
            placeholder="密码"
            class="gate-input"
            @keydown.enter="handleSubmit"
            :disabled="checking"
          />
          <button
            class="gate-btn"
            @click="handleSubmit"
            :disabled="!password.trim() || checking"
          >
            {{ checking ? '验证中...' : '进入' }}
          </button>
        </div>
        <p v-if="error" class="gate-error">{{ error }}</p>
      </div>

      <div v-else class="gate-authed">
        <p class="gate-welcome">✦ 欢迎回来</p>
        <button class="gate-enter-btn" @click="enterApp">
          进入应用 →
        </button>
      </div>

      <p class="gate-footer">仅供学习交流使用</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const password = ref('')
const error = ref('')
const checking = ref(false)
const authed = ref(false)

// 从环境变量读取密码（Vercel dashboard 中设置 VITE_ACCESS_PASSWORD）
const ACCESS_PASSWORD = import.meta.env.VITE_ACCESS_PASSWORD || 'wuzhixue'

onMounted(async () => {
  // 检查 localStorage 是否已认证
  const gatePassed = localStorage.getItem('wuzhixue_gate')
  if (gatePassed === 'true') {
    authed.value = true
    // delay then auto-enter
    setTimeout(() => enterApp(), 800)
  } else {
    await nextTick()
    document.querySelector('.gate-input')?.focus()
  }
})

function handleSubmit() {
  if (!password.value.trim()) return
  error.value = ''
  checking.value = true
  // 模拟短暂延迟，防止暴力穷举（纯前端验证，聊胜于无）
  setTimeout(() => {
    if (password.value === ACCESS_PASSWORD) {
      localStorage.setItem('wuzhixue_gate', 'true')
      authed.value = true
      setTimeout(() => enterApp(), 600)
    } else {
      error.value = '密码错误，请重试'
      checking.value = false
      password.value = ''
    }
  }, 300)
}

function enterApp() {
  router.push('/chat')
}
</script>

<style scoped>
.gate {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--bg-page);

  /* 网格纹理 */
  background-image:
    linear-gradient(rgba(27, 42, 74, 0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(27, 42, 74, 0.025) 1px, transparent 1px);
  background-size: 24px 24px;
  background-position: -1px -1px;
}

.gate-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 48px 40px 36px;
  width: 100%;
  max-width: 400px;
  text-align: center;
  box-shadow: var(--shadow-lg);
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.gate-brand {
  margin-bottom: 32px;
}

.gate-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 12px;
  line-height: 1;
}

.gate-title {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 900;
  color: var(--ink-900);
  letter-spacing: 0.04em;
  margin: 0 0 6px;
}

.gate-subtitle {
  font-size: 14px;
  color: var(--neutral-500);
  margin: 0;
}

.gate-hint {
  font-size: 14px;
  color: var(--neutral-600);
  margin: 0 0 16px;
}

.input-group {
  display: flex;
  gap: 10px;
}

.gate-input {
  flex: 1;
  padding: 12px 16px;
  border: 1.5px solid var(--neutral-300);
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 15px;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  color: var(--text-primary);
  background: var(--bg-elevated);
}
.gate-input:focus {
  border-color: var(--ink-700);
  box-shadow: 0 0 0 3px rgba(43, 74, 122, 0.08);
}
.gate-input::placeholder {
  color: var(--neutral-400);
}

.gate-btn {
  padding: 12px 24px;
  background: var(--ink-900);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.gate-btn:hover:not(:disabled) {
  background: var(--ink-800);
}
.gate-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.gate-error {
  margin-top: 12px;
  font-size: 13px;
  color: var(--rose-600);
  animation: fadeIn 0.2s;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* ── 已认证状态 ── */
.gate-authed {
  animation: fadeIn 0.4s;
}

.gate-welcome {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0 0 20px;
}

.gate-enter-btn {
  padding: 12px 36px;
  background: var(--amber-600);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.gate-enter-btn:hover {
  background: #B45309;
  box-shadow: var(--shadow-glow);
}

.gate-footer {
  margin-top: 32px;
  font-size: 12px;
  color: var(--neutral-400);
}
</style>
