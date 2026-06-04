<template>
  <div class="journey-view page-ambient fade-in-up">
    <div class="page-header">
      <h2>📅 学习历程</h2>
      <div class="header-period">
        <button class="period-btn" :class="{ active: period === 'month' }" @click="period = 'month'">月</button>
        <button class="period-btn" :class="{ active: period === 'all' }" @click="period = 'all'">全部</button>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>加载学习历程...</p>
    </div>

    <template v-else-if="journey">
      <!-- ═══ 统计概览 ═══ -->
      <div class="stats-row">
        <div class="stat-card">
          <span class="stat-icon">📆</span>
          <div class="stat-body">
            <span class="stat-num">{{ journey.total_days }}</span>
            <span class="stat-label">学习天数</span>
          </div>
        </div>
        <div class="stat-card">
          <span class="stat-icon">🔥</span>
          <div class="stat-body">
            <span class="stat-num">{{ journey.streak }}</span>
            <span class="stat-label">连续天数</span>
          </div>
        </div>
        <div class="stat-card">
          <span class="stat-icon">📚</span>
          <div class="stat-body">
            <span class="stat-num">{{ journey.subjects_covered.length }}</span>
            <span class="stat-label">涉及科目</span>
          </div>
        </div>
        <div class="stat-card">
          <span class="stat-icon">💬</span>
          <div class="stat-body">
            <span class="stat-num">{{ totalActivities }}</span>
            <span class="stat-label">活动次数</span>
          </div>
        </div>
      </div>

      <!-- 科目标签 -->
      <div v-if="journey.subjects_covered.length > 0" class="subjects-row">
        <span v-for="s in journey.subjects_covered" :key="s" class="subject-chip">{{ s }}</span>
      </div>

      <!-- ═══ 日历热力图 ═══ -->
      <div class="heatmap-section">
        <h3 class="section-title"><span>📊</span> 学习热力图</h3>
        <div class="heatmap-container">
          <div v-for="(days, ym) in journey.heatmap" :key="ym" class="heatmap-month">
            <div class="heatmap-month-label">{{ ym }}</div>
            <div class="heatmap-grid">
              <div
                v-for="(intensity, dayNum) in sortedDays(days)"
                :key="dayNum"
                class="heatmap-cell"
                :class="intensityClass(intensity)"
                :title="`${ym}-${dayNum}: ${intensityLabel(intensity)}`"
              ></div>
            </div>
          </div>
          <div v-if="Object.keys(journey.heatmap || {}).length === 0" class="heatmap-empty">
            还没有学习记录，去聊聊天或刷几道题吧 ✨
          </div>
        </div>
        <div class="heatmap-legend">
          <span>少</span>
          <span class="legend-cell legend-0"></span>
          <span class="legend-cell legend-1"></span>
          <span class="legend-cell legend-2"></span>
          <span class="legend-cell legend-3"></span>
          <span class="legend-cell legend-4"></span>
          <span>多</span>
        </div>
      </div>

      <!-- ═══ 时间轴 ═══ -->
      <div class="timeline-section">
        <h3 class="section-title"><span>📜</span> 每日记录</h3>

        <div v-if="filteredDays.length === 0" class="timeline-empty">
          还没有学习记录 ✨
        </div>

        <div class="timeline">
          <div v-for="(day, idx) in filteredDays" :key="day.date" class="timeline-item">
            <div class="timeline-dot" :class="dotClass(day.intensity)"></div>
            <div v-if="idx < filteredDays.length - 1" class="timeline-line"></div>

            <div class="timeline-card">
              <div class="tl-header">
                <span class="tl-date">{{ formatDate(day.date) }}</span>
                <span class="tl-intensity" :class="intensityLabel(day.intensity)">
                  {{ intensityLabel(day.intensity) }}
                </span>
              </div>

              <!-- 活动标签 -->
              <div v-if="day.activities.length > 0" class="tl-activities">
                <span
                  v-for="act in day.activities"
                  :key="act.type"
                  :class="['tl-activity', `act-${act.type}`]"
                >
                  {{ activityIcon(act.type) }}
                  {{ act.label }}
                  <template v-if="act.type === 'practice'">
                    {{ act.count }}题·{{ act.rate }}%
                  </template>
                  <template v-else>
                    ×{{ act.count }}
                  </template>
                </span>
              </div>

              <!-- 知识点标签 -->
              <div v-if="day.subjects.length > 0" class="tl-subjects">
                <span v-for="s in day.subjects" :key="s" class="mini-chip">{{ s }}</span>
              </div>

              <!-- 学习摘要 -->
              <p v-if="day.summary" class="tl-summary">{{ day.summary }}</p>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 无数据 -->
    <div v-else class="empty-state">
      <div class="empty-icon">📅</div>
      <p class="empty-title">还没有学习记录</p>
      <p class="empty-hint">开始使用答疑、刷题功能后，这里会记录你的学习历程</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getJourney } from '../api/analysis'

const loading = ref(true)
const journey = ref(null)
const period = ref('month')

onMounted(async () => {
  try {
    const res = await getJourney()
    journey.value = res
  } catch {
    journey.value = null
  } finally {
    loading.value = false
  }
})

const totalActivities = computed(() => {
  if (!journey.value?.days) return 0
  return journey.value.days.reduce((sum, d) => {
    return sum + d.activities.reduce((s, a) => s + (a.count || 1), 0)
  }, 0)
})

const filteredDays = computed(() => {
  if (!journey.value?.days) return []
  if (period.value === 'all') return journey.value.days
  // 只显示最近 30 天
  return journey.value.days.slice(0, 30)
})

function sortedDays(days) {
  return Object.entries(days).sort(([a], [b]) => Number(a) - Number(b))
}

function intensityClass(intensity) {
  if (intensity === 0) return 'legend-0'
  if (intensity <= 0.25) return 'legend-1'
  if (intensity <= 0.5) return 'legend-2'
  if (intensity <= 0.75) return 'legend-3'
  return 'legend-4'
}

function intensityLabel(intensity) {
  if (intensity === 0) return '无'
  if (intensity <= 0.25) return '轻'
  if (intensity <= 0.5) return '中'
  if (intensity <= 0.75) return '良'
  return '高'
}

function dotClass(intensity) {
  if (intensity <= 0.25) return 'dot-low'
  if (intensity <= 0.5) return 'dot-mid'
  if (intensity <= 0.75) return 'dot-good'
  return 'dot-high'
}

function activityIcon(type) {
  const icons = { chat: '💬', practice: '✏️', review: '📝', lab: '🔬' }
  return icons[type] || '📌'
}

function formatDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  const month = d.getMonth() + 1
  const day = d.getDate()
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  return `${month}月${day}日 周${weekdays[d.getDay()]}`
}
</script>

<style scoped>
.journey-view {
  max-width: 780px;
  margin: 0 auto;
  padding-bottom: 40px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-header h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--ink-900);
}
.header-period {
  display: flex;
  gap: 4px;
  background: var(--neutral-100);
  border-radius: 8px;
  padding: 3px;
}
.period-btn {
  padding: 5px 14px;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--neutral-600);
  cursor: pointer;
  transition: all 0.15s;
}
.period-btn.active {
  background: #fff;
  color: var(--ink-900);
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

/* ── 统计 ── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
  box-shadow: var(--shadow-sm);
}
.stat-icon {
  font-size: 24px;
  line-height: 1;
}
.stat-body {
  display: flex;
  flex-direction: column;
}
.stat-num {
  font-size: 22px;
  font-weight: 800;
  color: var(--ink-900);
  font-family: var(--font-display);
  line-height: 1.2;
}
.stat-label {
  font-size: 12px;
  color: var(--neutral-500);
  font-weight: 500;
}

/* ── 科目 ── */
.subjects-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}
.subject-chip {
  background: var(--ink-50);
  color: var(--ink-700);
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
}

/* ── 区块标题 ── */
.section-title {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 700;
  margin: 0 0 14px;
  color: var(--ink-900);
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ── 热力图 ── */
.heatmap-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-sm);
}
.heatmap-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.heatmap-month {
  display: flex;
  align-items: center;
  gap: 12px;
}
.heatmap-month-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--neutral-500);
  width: 56px;
  flex-shrink: 0;
  text-align: right;
}
.heatmap-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.heatmap-cell {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  transition: transform 0.15s;
}
.heatmap-cell:hover {
  transform: scale(1.4);
}
.heatmap-empty {
  text-align: center;
  color: var(--neutral-400);
  font-size: 13px;
  padding: 20px;
}
.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 10px;
  justify-content: flex-end;
  font-size: 11px;
  color: var(--neutral-400);
}
.legend-cell {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}
.legend-0 { background: var(--neutral-100); }
.legend-1 { background: #FEF3C7; }
.legend-2 { background: #FCD34D; }
.legend-3 { background: #F59E0B; }
.legend-4 { background: #D97706; }

/* ── 时间轴 ── */
.timeline-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
}
.timeline-empty {
  text-align: center;
  padding: 40px;
  color: var(--neutral-500);
  font-size: 14px;
}

.timeline {
  position: relative;
  padding-left: 28px;
}
.timeline-item {
  position: relative;
  padding-bottom: 20px;
}
.timeline-dot {
  position: absolute;
  left: -28px;
  top: 4px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 3px solid var(--surface);
}
.dot-low {
  background: var(--neutral-300);
  box-shadow: 0 0 0 2px var(--neutral-300);
}
.dot-mid {
  background: #FCD34D;
  box-shadow: 0 0 0 2px #FCD34D;
}
.dot-good {
  background: #F59E0B;
  box-shadow: 0 0 0 2px #F59E0B;
}
.dot-high {
  background: var(--amber-600);
  box-shadow: 0 0 0 2px var(--amber-600);
}
.timeline-line {
  position: absolute;
  left: -21px;
  top: 18px;
  bottom: 0;
  width: 2px;
  background: var(--neutral-200);
}

.timeline-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 18px;
  transition: box-shadow 0.2s;
}
.timeline-card:hover {
  box-shadow: var(--shadow-sm);
}

.tl-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.tl-date {
  font-size: 14px;
  font-weight: 700;
  color: var(--ink-900);
}
.tl-intensity {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 8px;
}
.tl-intensity.轻 {
  background: var(--neutral-100);
  color: var(--neutral-500);
}
.tl-intensity.中 {
  background: #FEF3C7;
  color: #92400E;
}
.tl-intensity.良 {
  background: #FDE68A;
  color: #92400E;
}
.tl-intensity.高 {
  background: var(--amber-100);
  color: #78350F;
}

/* ── 活动标签 ── */
.tl-activities {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.tl-activity {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 12px;
  white-space: nowrap;
}
.act-chat {
  background: #E0E7FF;
  color: #3730A3;
}
.act-practice {
  background: #D1FAE5;
  color: #065F46;
}
.act-review {
  background: #FEE2E2;
  color: #991B1B;
}
.act-lab {
  background: #F3E8FF;
  color: #6B21A8;
}

.tl-subjects {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.mini-chip {
  background: var(--ink-50);
  color: var(--ink-700);
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}
.tl-summary {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

/* ── 通用 ── */
.loading-state, .empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--neutral-500);
}
.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--neutral-200);
  border-top-color: var(--amber-600);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 6px;
}
.empty-hint {
  font-size: 14px;
  color: var(--neutral-500);
  margin: 0;
}
</style>
