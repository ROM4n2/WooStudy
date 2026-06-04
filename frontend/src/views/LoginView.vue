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
            <button class="support-trigger" @click="showSupportModal = true">
              💡 如果可以，填我的邀请码支持一下 →
            </button>
          </div>
        </div>

        <!-- 支持弹窗 -->
        <Teleport to="body">
          <div v-if="showSupportModal" class="modal-overlay" @click.self="showSupportModal = false">
            <div class="modal-card">
              <button class="modal-close" @click="showSupportModal = false">✕</button>
              <div class="modal-emoji">🙏</div>
              <h3 class="modal-title">支持一下开发者</h3>
              <p class="modal-text">
                如果你觉得 WooStudy 对你有帮助，在注册 Mimo 时填上我的邀请码，就是对我最大的支持 ❤️
              </p>
              <div class="modal-code-box">
                <code class="modal-code">{{ mimoInviteCode }}</code>
                <button class="modal-copy-btn" @click="copyInviteCode">
                  {{ copied ? '已复制 ✓' : '复制邀请码' }}
                </button>
              </div>
              <p class="modal-hint">
                注册 Mimo 时填入邀请码，你我都能获得额外额度 🎁
              </p>
              <a :href="mimoRegisterUrl" target="_blank" class="modal-link" @click="showSupportModal = false">
                去 Mimo 注册 →
              </a>
            </div>
          </div>
        </Teleport>

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
const showSupportModal = ref(false)
const mimoInviteCode = ref('')
const mimoRegisterUrl = ref('https://platform.xiaomimimo.com/')

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
/* ══ 登录页（深色渐变氛围） ══ */
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--bg-page);
  background-image:
    radial-gradient(ellipse at 20% 50%, rgba(217, 119, 6, 0.04) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(27, 42, 74, 0.03) 0%, transparent 50%),
    linear-gradient(rgba(27, 42, 74, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(27, 42, 74, 0.02) 1px, transparent 1px);
  background-size: auto, auto, 28px 28px, 28px 28px;
  background-position: -1px -1px;
}

.login-card {
  background: var(--surface-glass);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border);
  border-radius: var(--radius-2xl);
  padding: 44px 40px 36px;
  width: 100%;
  max-width: 440px;
  box-shadow: var(--shadow-lg);
  animation: cardIn 0.55s var(--ease-out-soft);
}
@keyframes cardIn {
  from { opacity: 0; transform: translateY(24px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* ══ 品牌区 ══ */
.login-brand {
  text-align: center;
  margin-bottom: 28px;
}
.brand-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 10px;
  line-height: 1;
  animation: brandFloat 3s var(--ease-out-soft) infinite;
}
@keyframes brandFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}
.brand-title {
  font-family: var(--font-display);
  font-size: 30px;
  font-weight: 900;
  color: var(--ink-900);
  letter-spacing: 0.04em;
  margin: 0 0 4px;
  background: var(--grad-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.brand-subtitle {
  font-size: 14px;
  color: var(--neutral-500);
  margin: 0;
}

/* ══ Tab 切换（胶囊式） ══ */
.tab-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  padding: 4px;
  border-radius: var(--radius);
  background: var(--neutral-100);
}
.tab {
  flex: 1;
  padding: 9px;
  border: none;
  background: transparent;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  color: var(--neutral-500);
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out-soft);
  border-radius: var(--radius-sm);
}
.tab.active {
  background: var(--surface);
  color: var(--ink-900);
  box-shadow: var(--shadow-xs);
}

/* ══ 表单 ══ */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.field { display: flex; flex-direction: column; gap: 5px; }
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
  transition: color var(--duration-fast);
}
.field-link:hover { color: var(--ink-900); text-decoration: underline; }

.field-input {
  padding: 10px 14px;
  border: 1.5px solid var(--neutral-300);
  border-radius: var(--radius);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--text-primary);
  outline: none;
  transition: all var(--duration-normal) var(--ease-out-soft);
  background: var(--bg-elevated);
}
.field-input:focus {
  border-color: var(--amber-500);
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.08);
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
  font-weight: 500;
}

.submit-btn {
  padding: 12px;
  background: var(--grad-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out-soft);
  margin-top: 4px;
  box-shadow: 0 2px 8px rgba(27, 42, 74, 0.12);
}
.submit-btn:hover:not(:disabled) {
  box-shadow: 0 4px 16px rgba(27, 42, 74, 0.18);
  transform: translateY(-1px);
}
.submit-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  transform: none;
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
.form-switch a:hover { text-decoration: underline; }

/* ══ Mimo 邀请码卡片 ══ */
.invite-card {
  display: flex;
  gap: 12px;
  padding: 14px;
  background: linear-gradient(135deg, var(--amber-50) 0%, var(--bg-elevated) 100%);
  border: 1px solid var(--amber-200);
  border-left: 4px solid var(--amber-600);
  border-radius: var(--radius);
}
.invite-icon { font-size: 28px; line-height: 1; }
.invite-body { flex: 1; }
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
  transition: all var(--duration-fast);
}
.copy-btn:hover { background: var(--amber-700); }

.support-trigger {
  margin-top: 10px;
  padding: 0;
  background: none;
  border: none;
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--ink-700);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
  text-decoration-color: var(--amber-300);
  transition: color var(--duration-fast);
}
.support-trigger:hover { color: #92400E; }

/* ══ 弹窗遮罩 ══ */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 24px;
  animation: fadeIn 0.2s var(--ease-out-soft);
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.modal-card {
  background: var(--surface);
  border-radius: var(--radius-xl);
  padding: 36px 32px 28px;
  max-width: 400px;
  width: 100%;
  text-align: center;
  box-shadow: var(--shadow-xl);
  animation: modalIn 0.35s var(--ease-spring);
  position: relative;
}
@keyframes modalIn {
  from { opacity: 0; transform: scale(0.92) translateY(12px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.modal-close {
  position: absolute;
  top: 12px;
  right: 14px;
  background: none;
  border: none;
  font-size: 18px;
  color: var(--neutral-400);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-xs);
  transition: all var(--duration-fast);
}
.modal-close:hover { background: var(--neutral-100); color: var(--neutral-700); }
.modal-emoji { font-size: 48px; line-height: 1; margin-bottom: 12px; }
.modal-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 800;
  color: var(--ink-900);
  margin: 0 0 10px;
}
.modal-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--neutral-600);
  margin: 0 0 18px;
}
.modal-code-box {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
}
.modal-code {
  padding: 8px 16px;
  background: var(--amber-50);
  border: 2px dashed var(--amber-500);
  border-radius: var(--radius);
  font-family: var(--font-mono);
  font-size: 18px;
  font-weight: 800;
  color: var(--ink-900);
  letter-spacing: 0.12em;
}
.modal-copy-btn {
  padding: 8px 16px;
  background: var(--amber-600);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--duration-fast);
}
.modal-copy-btn:hover { background: var(--amber-700); }
.modal-hint {
  font-size: 12px;
  color: var(--neutral-400);
  margin: 0 0 16px;
}
.modal-link {
  display: inline-block;
  padding: 10px 28px;
  background: var(--grad-primary);
  color: #fff;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  transition: all var(--duration-normal) var(--ease-out-soft);
  box-shadow: 0 2px 8px rgba(27, 42, 74, 0.1);
}
.modal-link:hover {
  box-shadow: 0 4px 16px rgba(27, 42, 74, 0.16);
  transform: translateY(-1px);
}
</style>
