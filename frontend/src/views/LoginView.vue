<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-brand">
        <span class="brand-icon">⚛️</span>
        <h1 class="brand-title">WooStudy</h1>
        <p class="brand-subtitle">高中物理 AI 助学</p>
      </div>

      <!-- Tab 切换 -->
      <div class="tab-bar">
        <button :class="['tab', { active: tab === 'login' }]" @click="tab = 'login'">
          登录
        </button>
        <button :class="['tab', { active: tab === 'register' }]" @click="tab = 'register'">
          注册
        </button>
      </div>

      <!-- ═══ 登录面板 ═══ -->
      <form v-if="tab === 'login'" class="login-form" @submit.prevent="handleLogin">
        <div class="field">
          <label class="field-label">用户名</label>
          <input v-model="loginForm.username" class="field-input" placeholder="输入用户名" required />
        </div>
        <div class="field">
          <label class="field-label">密码</label>
          <input v-model="loginForm.password" type="password" class="field-input" placeholder="输入密码" required />
        </div>
        <p v-if="loginError" class="form-error">{{ loginError }}</p>
        <button type="submit" class="submit-btn" :disabled="authStore.loading">
          {{ authStore.loading ? '登录中...' : '登录' }}
        </button>
        <p class="form-switch">
          还没有账号？
          <a href="#" @click.prevent="tab = 'register'">去注册 →</a>
        </p>
      </form>

      <!-- ═══ 注册面板 ═══ -->
      <form v-else class="login-form" @submit.prevent="handleRegister">
        <div class="field">
          <label class="field-label">用户名</label>
          <input v-model="regForm.username" class="field-input" placeholder="3-20位，中文/字母/数字" required />
        </div>
        <div class="field">
          <label class="field-label">密码</label>
          <input v-model="regForm.password" type="password" class="field-input" placeholder="至少6位" required />
        </div>
        <div class="field">
          <label class="field-label">确认密码</label>
          <input v-model="regForm.confirm" type="password" class="field-input" placeholder="再次输入密码" required />
        </div>

        <div class="field-divider">
          <span>API Key 设置</span>
        </div>
        <p class="field-hint">需要 Mimo 和 DeepSeek 的 API Key 才能使用 AI 功能</p>

        <div class="field">
          <label class="field-label">
            Mimo API Key
            <a :href="mimoRegisterUrl" target="_blank" class="field-link">注册获取 →</a>
          </label>
          <input v-model="regForm.mimoKey" class="field-input" placeholder="sk-xxxxxxxx" required />
        </div>
        <div class="field">
          <label class="field-label">
            DeepSeek API Key
            <a href="https://platform.deepseek.com/api_keys" target="_blank" class="field-link">注册获取 →</a>
          </label>
          <input v-model="regForm.deepseekKey" class="field-input" placeholder="sk-xxxxxxxx" required />
        </div>

        <!-- Mimo 邀请码展示 -->
        <div v-if="mimoInviteCode" class="invite-card">
          <div class="invite-icon">🎁</div>
          <div class="invite-body">
            <p class="invite-title">Mimo 邀请码</p>
            <p class="invite-desc">注册 Mimo 时填入以下邀请码，可享福利：</p>
            <div class="invite-code-row">
              <code class="invite-code">{{ mimoInviteCode }}</code>
              <button class="copy-btn" @click="copyInviteCode">{{ copied ? '已复制 ✓' : '复制' }}</button>
            </div>
          </div>
        </div>

        <p v-if="regError" class="form-error">{{ regError }}</p>
        <button type="submit" class="submit-btn" :disabled="authStore.loading">
          {{ authStore.loading ? '注册中...' : '注册并进入' }}
        </button>
        <p class="form-switch">
          已有账号？
          <a href="#" @click.prevent="tab = 'login'">去登录 →</a>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const tab = ref('login')
const copied = ref(false)
const mimoInviteCode = ref('')
const mimoRegisterUrl = ref('https://console.xiaomimimo.com/register')

// 登录表单
const loginForm = ref({ username: '', password: '' })
const loginError = ref('')

// 注册表单
const regForm = ref({ username: '', password: '', confirm: '', mimoKey: '', deepseekKey: '' })
const regError = ref('')

onMounted(async () => {
  // 如果已登录，直接进入
  if (authStore.token) {
    const res = await authStore.fetchMe()
    if (res) {
      mimoInviteCode.value = res.mimo_invite_code || ''
      router.push('/chat')
    }
  }
})

async function handleLogin() {
  loginError.value = ''
  try {
    await authStore.login(loginForm.value.username, loginForm.value.password)
    router.push('/chat')
  } catch (e) {
    loginError.value = e.message
  }
}

async function handleRegister() {
  regError.value = ''
  const { username, password, confirm, mimoKey, deepseekKey } = regForm.value

  if (password !== confirm) {
    regError.value = '两次输入的密码不一致'
    return
  }
  if (username.length < 3) {
    regError.value = '用户名至少 3 个字符'
    return
  }
  if (password.length < 6) {
    regError.value = '密码至少 6 位'
    return
  }

  try {
    await authStore.register(username, password, mimoKey, deepseekKey)
    router.push('/chat')
  } catch (e) {
    regError.value = e.message
  }
}

async function copyInviteCode() {
  try {
    await navigator.clipboard.writeText(mimoInviteCode.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // fallback
    const ta = document.createElement('textarea')
    ta.value = mimoInviteCode.value
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--bg-page);
  background-image:
    linear-gradient(rgba(27, 42, 74, 0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(27, 42, 74, 0.025) 1px, transparent 1px);
  background-size: 24px 24px;
  background-position: -1px -1px;
}

.login-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 40px 36px 32px;
  width: 100%;
  max-width: 440px;
  box-shadow: var(--shadow-lg);
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.login-brand {
  text-align: center;
  margin-bottom: 28px;
}
.brand-icon {
  font-size: 44px;
  display: block;
  margin-bottom: 10px;
  line-height: 1;
}
.brand-title {
  font-family: var(--font-display);
  font-size: 30px;
  font-weight: 900;
  color: var(--ink-900);
  letter-spacing: 0.04em;
  margin: 0 0 4px;
}
.brand-subtitle {
  font-size: 14px;
  color: var(--neutral-500);
  margin: 0;
}

/* Tab 切换 */
.tab-bar {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1.5px solid var(--neutral-200);
}
.tab {
  flex: 1;
  padding: 10px;
  border: none;
  background: var(--surface);
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  color: var(--neutral-500);
  cursor: pointer;
  transition: all 0.2s;
}
.tab:first-child {
  border-right: 1px solid var(--neutral-200);
}
.tab.active {
  background: var(--ink-900);
  color: #fff;
}

/* 表单 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.field-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--neutral-700);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.field-link {
  font-size: 12px;
  font-weight: 500;
  color: var(--ink-700);
  text-decoration: none;
}
.field-link:hover {
  text-decoration: underline;
}
.field-input {
  padding: 10px 14px;
  border: 1.5px solid var(--neutral-300);
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  background: var(--bg-elevated);
}
.field-input:focus {
  border-color: var(--ink-700);
  box-shadow: 0 0 0 3px rgba(43, 74, 122, 0.08);
}

.field-divider {
  text-align: center;
  position: relative;
  margin: 4px 0;
}
.field-divider::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  width: 100%;
  height: 1px;
  background: var(--neutral-200);
}
.field-divider span {
  position: relative;
  background: var(--surface);
  padding: 0 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--neutral-500);
}

.field-hint {
  font-size: 12px;
  color: var(--neutral-400);
  margin: -8px 0 0;
  text-align: center;
}

.form-error {
  font-size: 13px;
  color: var(--rose-600);
  margin: 0;
  text-align: center;
}

.submit-btn {
  padding: 12px;
  background: var(--ink-900);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 4px;
}
.submit-btn:hover:not(:disabled) {
  background: var(--ink-800);
}
.submit-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.form-switch {
  text-align: center;
  font-size: 13px;
  color: var(--neutral-500);
  margin: 0;
}
.form-switch a {
  color: var(--ink-700);
  font-weight: 600;
  text-decoration: none;
}
.form-switch a:hover {
  text-decoration: underline;
}

/* Mimo 邀请码卡片 */
.invite-card {
  display: flex;
  gap: 12px;
  padding: 14px;
  background: var(--amber-50);
  border: 1px solid var(--amber-400);
  border-left: 4px solid var(--amber-600);
  border-radius: var(--radius-sm);
}
.invite-icon {
  font-size: 28px;
  line-height: 1;
}
.invite-body {
  flex: 1;
}
.invite-title {
  font-weight: 700;
  font-size: 14px;
  color: #92400E;
  margin: 0 0 2px;
}
.invite-desc {
  font-size: 12px;
  color: #A16207;
  margin: 0 0 8px;
}
.invite-code-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.invite-code {
  flex: 1;
  padding: 6px 10px;
  background: #fff;
  border: 1px dashed var(--amber-500);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--ink-900);
  letter-spacing: 0.1em;
  text-align: center;
}
.copy-btn {
  padding: 6px 14px;
  background: var(--amber-600);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
}
.copy-btn:hover {
  background: #B45309;
}
</style>
