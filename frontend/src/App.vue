<template>
  <div id="app-container">
    <nav class="top-nav">
      <div class="nav-brand">
        <span class="brand-icon">⚛️</span>
        <div class="brand-text-group">
          <span class="brand-text">物知学</span>
          <span class="brand-tag">高中物理 AI 助学</span>
        </div>
      </div>
      <div class="nav-links">
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
    </nav>
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

/* ── 主内容区 ── */
.main-content {
  flex: 1;
  padding: 28px 32px 40px;
  max-width: 1120px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

/* ── 页面过渡动画 ── */
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
