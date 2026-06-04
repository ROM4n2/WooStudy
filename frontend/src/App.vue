<template>
  <div id="app-container">
    <nav class="top-nav">
      <div class="nav-brand">
        <span class="brand-icon">⚛️</span>
        <div class="brand-text-group">
          <span class="brand-text">WooStudy</span>
          <span class="brand-tag">高中物理 AI 助学</span>
        </div>
      </div>
      <div class="nav-right">
        <div class="nav-links" v-if="authStore.isLoggedIn">
          <router-link to="/chat" class="nav-link">
            <span class="nav-icon">💬</span>
            <span class="nav-label">答疑</span>
          </router-link>
          <router-link to="/errorbook" class="nav-link">
            <span class="nav-icon">📝</span>
            <span class="nav-label">错题本</span>
          </router-link>
          <router-link to="/practice" class="nav-link">
            <span class="nav-icon">✏️</span>
            <span class="nav-label">刷题</span>
          </router-link>
          <router-link to="/lab" class="nav-link">
            <span class="nav-icon">🔬</span>
            <span class="nav-label">实验室</span>
          </router-link>
          <router-link to="/analysis" class="nav-link">
            <span class="nav-icon">📊</span>
            <span class="nav-label">学情</span>
          </router-link>
        </div>
        <div v-if="authStore.isLoggedIn" class="user-area">
          <button class="settings-btn" @click="showSettings = !showSettings" title="设置">
            ⚙️
          </button>
          <span class="user-name">{{ authStore.user?.username }}</span>
          <button class="logout-btn" @click="handleLogout">退出</button>
        </div>
      </div>
    </nav>

    <!-- 设置面板 -->
    <div v-if="showSettings" class="settings-overlay" @click.self="showSettings = false">
      <div class="settings-panel">
        <div class="settings-header">
          <h3>⚙️ 设置</h3>
          <button class="close-btn" @click="showSettings = false">✕</button>
        </div>
        <div class="settings-body">
          <div class="settings-section">
            <h4>API Key</h4>
            <p class="hint">修改你的 API Key（Mimo 和 DeepSeek 都需要）</p>
            <div class="field">
              <label>Mimo API Key</label>
              <input v-model="settingsForm.mimoKey" class="field-input" placeholder="sk-xxxxxxxx" />
            </div>
            <div class="field">
              <label>DeepSeek API Key</label>
              <input v-model="settingsForm.deepseekKey" class="field-input" placeholder="sk-xxxxxxxx" />
            </div>
            <p v-if="settingsMsg" class="settings-msg">{{ settingsMsg }}</p>
            <button class="submit-btn" @click="saveApiKeys" :disabled="savingKeys">
              {{ savingKeys ? '保存中...' : '保存' }}
            </button>
          </div>

          <!-- Mimo 邀请码展示 -->
          <div v-if="mimoInviteCode" class="settings-invite">
            <p class="invite-label">🎁 Mimo 邀请码</p>
            <div class="invite-code-row">
              <code class="invite-code">{{ mimoInviteCode }}</code>
              <button class="copy-btn" @click="copyInviteCode">{{ copied ? '已复制 ✓' : '复制' }}</button>
            </div>
            <p class="invite-hint">分享给同学注册 Mimo 时填入，可享福利</p>
          </div>
        </div>
      </div>
    </div>

    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const showSettings = ref(false)
const savingKeys = ref(false)
const settingsMsg = ref('')
const mimoInviteCode = ref('')
const copied = ref(false)

const settingsForm = ref({ mimoKey: '', deepseekKey: '' })

onMounted(async () => {
  if (authStore.token) {
    const res = await authStore.fetchMe()
    if (res) {
      mimoInviteCode.value = res.mimo_invite_code || ''
    }
  }
})

async function saveApiKeys() {
  savingKeys.value = true
  settingsMsg.value = ''
  try {
    await authStore.updateApiKeys(settingsForm.value.mimoKey, settingsForm.value.deepseekKey)
    settingsMsg.value = '✅ 保存成功！刷新页面后生效。'
    settingsForm.value = { mimoKey: '', deepseekKey: '' }
  } catch (e) {
    settingsMsg.value = '❌ ' + e.message
  } finally {
    savingKeys.value = false
  }
}

async function copyInviteCode() {
  try {
    await navigator.clipboard.writeText(mimoInviteCode.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
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

function handleLogout() {
  authStore.logout()
  router.push('/')
}
</script>

<style scoped>
#app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: transparent;
}

/* ── 导航栏 ── */
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  height: 64px;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--neutral-200);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-icon {
  font-size: 24px;
  line-height: 1;
  filter: saturate(1.2);
}
.brand-text-group {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.brand-text {
  font-family: var(--font-display);
  font-size: 21px;
  font-weight: 900;
  color: var(--ink-900);
  letter-spacing: 0.04em;
}
.brand-tag {
  font-size: 12px;
  color: var(--neutral-500);
  font-weight: 400;
  display: none;
}
@media (min-width: 640px) {
  .brand-tag { display: inline; }
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* ── 导航链接 ── */
.nav-links {
  display: flex;
  gap: 2px;
}
.nav-link {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  color: var(--neutral-600);
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  position: relative;
  transition: all 0.2s ease;
}
.nav-link::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%) scaleX(0);
  width: 60%;
  height: 2.5px;
  background: var(--ink-900);
  border-radius: 2px;
  transition: transform 0.25s ease;
}
.nav-link:hover {
  color: var(--ink-900);
  background: var(--ink-50);
}
.nav-link.router-link-active {
  color: var(--ink-900);
  font-weight: 600;
}
.nav-link.router-link-active::after {
  transform: translateX(-50%) scaleX(1);
}
.nav-icon {
  font-size: 14px;
  line-height: 1;
}
.nav-label {
  line-height: 1;
}

/* ── 用户区域 ── */
.user-area {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 12px;
  border-left: 1px solid var(--neutral-200);
}
.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-900);
}
.settings-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.15s;
}
.settings-btn:hover {
  background: var(--ink-50);
}
.logout-btn {
  padding: 5px 12px;
  border: 1.5px solid var(--neutral-300);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--neutral-600);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  font-family: var(--font-body);
}
.logout-btn:hover {
  border-color: var(--rose-600);
  color: var(--rose-600);
  background: var(--rose-50);
}

/* ── 设置面板 ── */
.settings-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.3);
  z-index: 200;
  display: flex;
  justify-content: flex-end;
  animation: fadeIn 0.2s;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
.settings-panel {
  width: 380px;
  max-width: 90vw;
  background: var(--surface);
  height: 100%;
  overflow-y: auto;
  box-shadow: -4px 0 24px rgba(0,0,0,0.1);
  animation: slideIn 0.25s ease-out;
}
@keyframes slideIn {
  from { transform: translateX(20px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border);
}
.settings-header h3 {
  margin: 0;
  font-size: 18px;
}
.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: var(--neutral-500);
  padding: 4px 8px;
  border-radius: 4px;
}
.close-btn:hover {
  background: var(--neutral-200);
}
.settings-body {
  padding: 24px;
}
.settings-section h4 {
  margin: 0 0 8px;
  font-size: 16px;
}
.hint {
  font-size: 13px;
  color: var(--neutral-500);
  margin: 0 0 16px;
}
.field {
  margin-bottom: 14px;
}
.field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--neutral-700);
  margin-bottom: 4px;
}
.field-input {
  width: 100%;
  padding: 9px 12px;
  border: 1.5px solid var(--neutral-300);
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 13px;
  outline: none;
  box-sizing: border-box;
  background: var(--bg-elevated);
}
.field-input:focus {
  border-color: var(--ink-700);
}
.settings-msg {
  font-size: 13px;
  margin: 8px 0;
  color: var(--teal-600);
}
.submit-btn {
  width: 100%;
  padding: 10px;
  background: var(--ink-900);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.submit-btn:hover:not(:disabled) {
  background: var(--ink-800);
}
.submit-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* 邀请码 */
.settings-invite {
  margin-top: 24px;
  padding: 16px;
  background: var(--amber-50);
  border: 1px solid var(--amber-400);
  border-radius: var(--radius-sm);
}
.invite-label {
  font-weight: 700;
  font-size: 14px;
  color: #92400E;
  margin: 0 0 8px;
}
.invite-code-row {
  display: flex;
  gap: 8px;
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
}
.copy-btn:hover {
  background: #B45309;
}
.invite-hint {
  font-size: 12px;
  color: #A16207;
  margin: 8px 0 0;
}

/* ── 主内容区 ── */
.main-content {
  flex: 1;
  padding: 28px 32px 40px;
  max-width: 1120px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

/* ── 页面过渡 ── */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
