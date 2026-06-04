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

      <div class="nav-center" v-if="authStore.isLoggedIn">
        <div class="nav-links">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="nav-link"
            :class="{ active: currentRoute === item.path }"
          >
            <span class="nav-icon">{{ item.icon }}</span>
            <span class="nav-label">{{ item.label }}</span>
            <span v-if="currentRoute === item.path" class="nav-glow"></span>
          </router-link>
        </div>
      </div>

      <div class="nav-right">
        <div v-if="authStore.isLoggedIn" class="user-area">
          <button class="settings-btn" @click="showSettings = !showSettings" title="设置">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
            </svg>
          </button>
          <span class="user-name">{{ authStore.user?.username }}</span>
          <button class="logout-btn" @click="handleLogout">退出</button>
        </div>

        <!-- 移动端汉堡菜单 -->
        <button
          v-if="authStore.isLoggedIn"
          class="menu-toggle"
          @click="mobileMenuOpen = !mobileMenuOpen"
          :aria-label="mobileMenuOpen ? '关闭菜单' : '打开菜单'"
        >
          <span :class="['hamburger', { open: mobileMenuOpen }]">
            <span></span><span></span><span></span>
          </span>
        </button>
      </div>
    </nav>

    <!-- 移动端导航抽屉 -->
    <div v-if="mobileMenuOpen" class="mobile-nav-overlay" @click.self="mobileMenuOpen = false">
      <div class="mobile-nav-drawer">
        <div class="mobile-nav-header">
          <span class="brand-icon">⚛️</span>
          <span class="brand-text">WooStudy</span>
        </div>
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="mobile-nav-link"
          :class="{ active: currentRoute === item.path }"
          @click="mobileMenuOpen = false"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="mobile-nav-label">{{ item.label }}</span>
          <span v-if="currentRoute === item.path" class="mobile-check">✓</span>
        </router-link>
        <div class="mobile-nav-footer">
          <span class="mobile-user">{{ authStore.user?.username }}</span>
          <button class="btn btn-ghost btn-sm" @click="handleLogout">退出登录</button>
        </div>
      </div>
    </div>

    <!-- 设置面板 -->
    <div v-if="showSettings" class="settings-overlay" @click.self="showSettings = false">
      <div class="settings-panel">
        <div class="settings-header">
          <h3>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:8px">
              <circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
            </svg>
            设置
          </h3>
          <button class="close-btn" @click="showSettings = false">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="settings-body">
          <div class="settings-section">
            <h4>API Key 管理</h4>
            <p class="hint">你的 API Key 仅存储在服务器数据库，安全加密</p>
            <div class="field">
              <label>Mimo API Key</label>
              <div class="input-wrap">
                <input v-model="settingsForm.mimoKey" class="field-input" placeholder="sk-xxxxxxxx" />
              </div>
            </div>
            <div class="field">
              <label>DeepSeek API Key</label>
              <div class="input-wrap">
                <input v-model="settingsForm.deepseekKey" class="field-input" placeholder="sk-xxxxxxxx" />
              </div>
            </div>
            <p v-if="settingsMsg" :class="['settings-msg', settingsMsg.includes('失败') ? 'error' : '']">{{ settingsMsg }}</p>
            <button class="btn btn-primary btn-lg save-btn" @click="saveApiKeys" :disabled="savingKeys">
              <span v-if="savingKeys" class="dots-loader"><span></span><span></span><span></span></span>
              <span v-else>保存 API Key</span>
            </button>
          </div>

          <hr class="divider-gradient" />

          <div v-if="mimoInviteCode" class="settings-invite">
            <p class="invite-label">🎁 Mimo 邀请码</p>
            <div class="invite-code-row">
              <code class="invite-code">{{ mimoInviteCode }}</code>
              <button :class="['btn', copied ? 'btn-primary' : 'btn-accent', 'btn-sm']" @click="copyInviteCode">
                {{ copied ? '已复制 ✓' : '复制' }}
              </button>
            </div>
            <p class="invite-hint">分享给同学注册 Mimo 时填入，可享福利</p>
          </div>
        </div>
      </div>
    </div>

    <main class="main-content" :data-page="currentRoute.replace('/', '') || 'login'">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" :key="currentRoute" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const showSettings = ref(false)
const mobileMenuOpen = ref(false)
const savingKeys = ref(false)
const settingsMsg = ref('')
const mimoInviteCode = ref('')
const copied = ref(false)

const currentRoute = computed(() => route.path)

const settingsForm = ref({ mimoKey: '', deepseekKey: '' })

const navItems = [
  { path: '/chat', icon: '💬', label: '答疑' },
  { path: '/errorbook', icon: '📝', label: '错题本' },
  { path: '/practice', icon: '✏️', label: '刷题' },
  { path: '/lab', icon: '🔬', label: '实验室' },
  { path: '/analysis', icon: '📊', label: '学情' },
  { path: '/journey', icon: '📅', label: '历程' },
  { path: '/knowledge', icon: '🧠', label: '图谱' },
  { path: '/contribute', icon: '✍️', label: '贡献' },
]

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
  mobileMenuOpen.value = false
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

/* ══ 导航栏 ══ */
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  height: 60px;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.brand-icon {
  font-size: 22px;
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
  font-size: 20px;
  font-weight: 900;
  color: var(--ink-900);
  letter-spacing: 0.04em;
}
.brand-tag {
  font-size: 11px;
  color: var(--neutral-500);
  font-weight: 400;
  display: none;
}
@media (min-width: 640px) {
  .brand-tag { display: inline; }
}

/* ══ 居中导航链接 ══ */
.nav-center {
  display: flex;
  justify-content: center;
  flex: 1;
}
.nav-links {
  display: flex;
  gap: 2px;
  background: var(--neutral-100);
  padding: 3px;
  border-radius: var(--radius);
}
.nav-link {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  color: var(--neutral-600);
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  position: relative;
  transition: all var(--duration-normal) var(--ease-out-soft);
  isolation: isolate;
}
.nav-link:hover {
  color: var(--ink-900);
  background: rgba(255,255,255,0.6);
}
.nav-link.active {
  color: var(--ink-900);
  font-weight: 600;
  background: var(--surface);
  box-shadow: var(--shadow-xs);
}
.nav-glow {
  position: absolute;
  bottom: -3px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 3px;
  background: var(--grad-accent);
  border-radius: 2px;
  animation: glowFadeIn 0.3s var(--ease-spring);
}
@keyframes glowFadeIn {
  from { opacity: 0; transform: translateX(-50%) scaleX(0); }
  to { opacity: 1; transform: translateX(-50%) scaleX(1); }
}
.nav-icon {
  font-size: 14px;
  line-height: 1;
}
.nav-label {
  line-height: 1;
}

/* ══ 用户区域 ══ */
.nav-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.user-area {
  display: flex;
  align-items: center;
  gap: 8px;
  display: none;
}
@media (min-width: 640px) {
  .user-area { display: flex; }
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
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  transition: all var(--duration-fast) var(--ease-out-soft);
  color: var(--neutral-500);
}
.settings-btn:hover {
  background: var(--ink-50);
  color: var(--ink-900);
  transform: rotate(30deg);
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
  transition: all var(--duration-fast) var(--ease-out-soft);
  font-family: var(--font-body);
}
.logout-btn:hover {
  border-color: var(--rose-600);
  color: var(--rose-600);
  background: var(--rose-50);
}

/* ══ 汉堡菜单 ══ */
.menu-toggle {
  display: flex;
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: var(--radius-sm);
  color: var(--neutral-600);
}
@media (min-width: 640px) {
  .menu-toggle { display: none; }
}
.menu-toggle:hover { color: var(--ink-900); }
.hamburger {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 20px;
}
.hamburger span {
  display: block;
  height: 2px;
  background: currentColor;
  border-radius: 1px;
  transition: all 0.25s var(--ease-out-soft);
}
.hamburger.open span:nth-child(1) {
  transform: translateY(6px) rotate(45deg);
}
.hamburger.open span:nth-child(2) {
  opacity: 0;
}
.hamburger.open span:nth-child(3) {
  transform: translateY(-6px) rotate(-45deg);
}

/* ══ 移动端导航抽屉 ══ */
.mobile-nav-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.3);
  z-index: 150;
  animation: fadeIn 0.2s;
}
.mobile-nav-drawer {
  width: 280px;
  max-width: 80vw;
  height: 100%;
  background: var(--surface);
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  box-shadow: 4px 0 24px rgba(0,0,0,0.1);
  animation: drawerSlideIn 0.25s var(--ease-out-soft);
}
@keyframes drawerSlideIn {
  from { transform: translateX(-20px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
.mobile-nav-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px 20px;
  border-bottom: 1px solid var(--border);
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 900;
  color: var(--ink-900);
}
.mobile-nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 24px;
  text-decoration: none;
  color: var(--neutral-700);
  font-size: 15px;
  font-weight: 500;
  transition: all var(--duration-fast) var(--ease-out-soft);
  border-left: 3px solid transparent;
}
.mobile-nav-link:hover {
  background: var(--ink-50);
  color: var(--ink-900);
}
.mobile-nav-link.active {
  background: var(--amber-50);
  color: var(--amber-700);
  border-left-color: var(--amber-500);
  font-weight: 600;
}
.mobile-nav-label { flex: 1; }
.mobile-check { color: var(--amber-600); font-weight: 700; }
.mobile-nav-footer {
  margin-top: auto;
  padding: 20px 24px;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.mobile-user {
  font-size: 13px;
  font-weight: 600;
  color: var(--neutral-600);
}

/* ══ 设置面板 ══ */
.settings-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.25);
  backdrop-filter: blur(4px);
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
  width: 400px;
  max-width: 92vw;
  background: var(--surface);
  height: 100%;
  overflow-y: auto;
  box-shadow: -4px 0 32px rgba(0,0,0,0.1);
  animation: slideIn 0.3s var(--ease-out-soft);
}
@keyframes slideIn {
  from { transform: translateX(30px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 28px;
  border-bottom: 1px solid var(--border);
}
.settings-header h3 {
  margin: 0;
  font-size: 18px;
}
.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: var(--radius-sm);
  color: var(--neutral-500);
  display: flex;
  align-items: center;
  transition: all var(--duration-fast) var(--ease-out-soft);
}
.close-btn:hover {
  background: var(--neutral-100);
  color: var(--neutral-900);
}
.settings-body {
  padding: 28px;
}
.settings-section h4 {
  margin: 0 0 8px;
  font-size: 16px;
}
.hint {
  font-size: 13px;
  color: var(--neutral-500);
  margin: 0 0 20px;
  line-height: 1.5;
}
.field {
  margin-bottom: 16px;
}
.field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--neutral-700);
  margin-bottom: 5px;
}
.input-wrap {
  position: relative;
}
.field-input {
  width: 100%;
  padding: 10px 14px;
  border: 1.5px solid var(--neutral-300);
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 13px;
  font-family: var(--font-mono);
  letter-spacing: 0.03em;
  outline: none;
  box-sizing: border-box;
  background: var(--bg-elevated);
  transition: all var(--duration-normal) var(--ease-out-soft);
}
.field-input:focus {
  border-color: var(--ink-700);
  box-shadow: 0 0 0 3px rgba(27, 42, 74, 0.08);
}
.settings-msg {
  font-size: 13px;
  margin: 12px 0;
  color: var(--teal-600);
  font-weight: 500;
}
.settings-msg.error {
  color: var(--rose-600);
}
.save-btn {
  width: 100%;
  margin-top: 8px;
  justify-content: center;
}

/* 邀请码 */
.settings-invite {
  padding: 20px;
  background: linear-gradient(135deg, var(--amber-50) 0%, var(--bg-elevated) 100%);
  border: 1px solid var(--amber-200);
  border-radius: var(--radius);
}
.invite-label {
  font-weight: 700;
  font-size: 14px;
  color: #92400E;
  margin: 0 0 10px;
}
.invite-code-row {
  display: flex;
  gap: 8px;
}
.invite-code {
  flex: 1;
  padding: 8px 12px;
  background: var(--surface);
  border: 1px dashed var(--amber-400);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--ink-900);
  letter-spacing: 0.1em;
  text-align: center;
}
.invite-hint {
  font-size: 12px;
  color: #A16207;
  margin: 10px 0 0;
}

/* ══ 主内容区 ══ */
.main-content {
  flex: 1;
  padding: 28px 32px 40px;
  max-width: 1120px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

/* ══ 页面过渡 ══ */
.page-fade-enter-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}
.page-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (max-width: 768px) {
  .top-nav { padding: 0 16px; height: 56px; }
  .nav-center { display: none; }
  .main-content { padding: 20px 16px 32px; }
  .settings-panel { width: 100%; max-width: 100%; }
}
</style>
