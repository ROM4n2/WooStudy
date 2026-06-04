<template>
  <div class="lab-view page-ambient fade-in-up">
    <div class="page-header">
      <h2>🔬 虚拟实验室</h2>
    </div>

    <!-- 实验分类导航 -->
    <div class="category-tabs">
      <button
        v-for="cat in categories"
        :key="cat"
        :class="['tab', { active: activeCategory === cat }]"
        @click="activeCategory = cat"
      >
        {{ cat }}
      </button>
    </div>

    <!-- 实验网格 -->
    <div class="lab-grid">
      <div
        v-for="lab in filteredLabs"
        :key="lab.id"
        :class="['lab-card', { active: activeLab?.id === lab.id }]"
        @click="openLab(lab)"
      >
        <div class="lab-icon">🔬</div>
        <div class="lab-name">{{ lab.name }}</div>
        <div class="lab-desc">{{ lab.description }}</div>
        <div class="lab-category">{{ lab.category }}</div>
      </div>
    </div>

    <!-- PhET 仿真 iframe -->
    <div v-if="activeLab" class="sim-container">
      <div class="sim-header">
        <h3>{{ activeLab.name }}</h3>
        <button class="btn-close" @click="handleCloseLab">✕ 关闭</button>
      </div>
      <iframe
        :src="activeLab.url"
        class="sim-iframe"
        allowfullscreen
        @load="onSimLoad"
      ></iframe>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getLabList, recordSession } from '../api/lab'

const categories = ['全部', '力学', '电学', '光学']
const activeCategory = ref('全部')
const activeLab = ref(null)
const labs = ref([])
const sessionStartTime = ref(null)

const filteredLabs = computed(() => {
  if (activeCategory.value === '全部') return labs.value
  return labs.value.filter(l => l.category === activeCategory.value)
})

onMounted(async () => {
  try {
    const res = await getLabList()
    labs.value = res.labs || []
  } catch { /* 静默 */ }
})

function openLab(lab) {
  recordCurrentSession()
  activeLab.value = lab
  sessionStartTime.value = Date.now()
}

async function recordCurrentSession() {
  if (activeLab.value && sessionStartTime.value) {
    const duration = Math.floor((Date.now() - sessionStartTime.value) / 1000)
    const labId = activeLab.value.id
    const labName = activeLab.value.name
    sessionStartTime.value = null  // 防止重复记录
    try {
      await recordSession(labId, labName, duration)
    } catch { /* 静默 */ }
  }
}

function handleCloseLab() {
  recordCurrentSession()
  activeLab.value = null
}

function onSimLoad() {
  // 自动记录实验开始（将在关闭时记录时长）
}

onUnmounted(() => {
  recordCurrentSession()
})
</script>

<style scoped>
/* ── 分类标签 ── */
.category-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 22px;
  flex-wrap: wrap;
}
.tab {
  padding: 7px 22px;
  border: 1.5px solid var(--neutral-300);
  border-radius: 20px;
  background: var(--surface);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--neutral-600);
  transition: all 0.2s ease;
  font-family: var(--font-body);
}
.tab:hover {
  border-color: var(--ink-500);
  color: var(--ink-700);
  background: var(--ink-50);
}
.tab.active {
  background: var(--ink-900);
  color: #fff;
  border-color: var(--ink-900);
  font-weight: 600;
}

/* ── 实验网格 ── */
.lab-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.lab-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid var(--teal-600);
  border-radius: var(--radius-lg);
  padding: 22px;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: var(--shadow-sm);
}
.lab-card:hover {
  border-color: var(--neutral-300);
  box-shadow: var(--shadow-md);
  transform: translateY(-3px);
}
.lab-card.active {
  border-left-color: var(--amber-600);
  background: var(--amber-50);
}

.lab-icon {
  font-size: 36px;
  margin-bottom: 10px;
  line-height: 1;
}
.lab-name {
  font-weight: 700;
  font-size: 16px;
  color: var(--ink-900);
  margin-bottom: 6px;
}
.lab-desc {
  font-size: 13px;
  color: var(--neutral-600);
  line-height: 1.6;
  margin-bottom: 10px;
}
.lab-category {
  font-size: 12px;
  font-weight: 600;
  color: var(--teal-600);
  background: var(--teal-50);
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
}

/* ── 仿真容器 ── */
.sim-container {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
}

.sim-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-elevated);
}
.sim-header h3 {
  font-family: var(--font-display);
  margin: 0;
  font-size: 17px;
  color: var(--ink-900);
}

.btn-close {
  background: none;
  border: 1.5px solid var(--neutral-300);
  border-radius: var(--radius-sm);
  padding: 6px 14px;
  cursor: pointer;
  color: var(--neutral-600);
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s;
  font-family: var(--font-body);
}
.btn-close:hover {
  background: var(--rose-50);
  border-color: var(--rose-600);
  color: var(--rose-600);
}

.sim-iframe {
  width: 100%;
  height: 600px;
  border: none;
}
</style>
