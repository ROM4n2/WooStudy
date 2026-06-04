<template>
  <div class="analysis-view">
    <div class="page-header">
      <h2>📊 学情分析</h2>
      <div class="header-actions">
        <button class="btn btn-outline" @click="showJourney = !showJourney">
          {{ showJourney ? '📋 查看报告' : '📅 学习历程' }}
        </button>
        <button class="btn btn-accent" @click="refreshReport" :disabled="loading">
          {{ loading ? '分析中...' : '🔄 刷新' }}
        </button>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>AI 正在分析你的学情数据...</p>
    </div>

    <!-- 无数据 -->
    <div v-else-if="!report && !showJourney" class="empty-state">
      <div class="empty-icon">📝</div>
      <p class="empty-title">还没有足够的做题数据</p>
      <p class="empty-hint">先去刷几道题吧！</p>
    </div>

    <!-- ═══════ 报告视图 ═══════ -->
    <div v-else-if="report && !showJourney" class="report">
      <div class="overview-cards">
        <div class="overview-card">
          <div class="ov-number">{{ report.total_questions }}</div>
          <div class="ov-label">总做题数</div>
        </div>
        <div class="overview-card">
          <div class="ov-number">{{ (report.total_correct_rate * 100).toFixed(0) }}%</div>
          <div class="ov-label">总正确率</div>
        </div>
        <div class="overview-card">
          <div class="ov-number">{{ journey?.streak || 0 }}<span class="ov-unit">天</span></div>
          <div class="ov-label">连续学习</div>
        </div>
      </div>

      <div class="section">
        <h3><span class="section-icon">📡</span> 知识点掌握度</h3>
        <div class="radar-container">
          <VChart :option="radarOption" autoresize style="height: 320px" />
        </div>
      </div>

      <div v-if="report.weaknesses?.length > 0" class="section">
        <h3><span class="section-icon">⚠️</span> 薄弱知识点</h3>
        <div v-for="(w, idx) in report.weaknesses" :key="idx" class="weakness-card">
          <div class="weakness-header">
            <span class="subject-tag">{{ w.subject }}</span>
            <span class="concept">{{ w.concept }}</span>
          </div>
          <div class="suggestion">💡 {{ w.suggestion }}</div>
        </div>
      </div>

      <div class="section summary-section">
        <h3><span class="section-icon">📋</span> 学习建议</h3>
        <p>{{ report.summary }}</p>
      </div>
    </div>

    <!-- ═══════ 学习历程视图 ═══════ -->
    <div v-else-if="journey && showJourney" class="journey">
      <div class="journey-header">
        <div class="journey-stat">
          <span class="stat-num">{{ journey.total_days }}</span>
          <span class="stat-label">学习天数</span>
        </div>
        <div class="journey-stat">
          <span class="stat-num">{{ journey.streak }}</span>
          <span class="stat-label">连续天数 🔥</span>
        </div>
        <div class="journey-stat">
          <span class="stat-num">{{ journey.subjects_covered.length }}</span>
          <span class="stat-label">涉及科目</span>
        </div>
      </div>

      <div v-if="journey.subjects_covered.length > 0" class="subjects-cloud">
        <span v-for="s in journey.subjects_covered" :key="s" class="subject-chip">{{ s }}</span>
      </div>

      <div class="timeline">
        <div v-if="journey.days.length === 0" class="empty-timeline">
          还没有学习记录，开启「追问模式」开始记录吧 ✨
        </div>
        <div v-for="(day, idx) in journey.days" :key="day.date" class="timeline-item">
          <div class="timeline-dot"></div>
          <div v-if="idx < journey.days.length - 1" class="timeline-line"></div>
          <div class="timeline-card">
            <div class="timeline-date">{{ formatDate(day.date) }}</div>
            <div class="timeline-subjects">
              <span v-for="s in day.subjects" :key="s" class="mini-chip">{{ s }}</span>
            </div>
            <p class="timeline-summary">{{ day.summary || '继续加油 💪' }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getReport, getJourney } from '../api/analysis'
import { use } from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

use([RadarChart, TooltipComponent, LegendComponent, CanvasRenderer])

const report = ref(null)
const journey = ref(null)
const loading = ref(true)
const showJourney = ref(false)

onMounted(async () => {
  await Promise.all([loadReport(), loadJourney()])
})

async function loadReport(forceRefresh = false) {
  loading.value = true
  try {
    const res = await getReport(forceRefresh)
    report.value = res
  } catch { report.value = null }
  finally { loading.value = false }
}

async function loadJourney() {
  try {
    const res = await getJourney()
    journey.value = res
  } catch { journey.value = null }
}

async function refreshReport() {
  await Promise.all([loadReport(true), loadJourney()])
}

function formatDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  const month = d.getMonth() + 1
  const day = d.getDate()
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  return `${month}月${day}日 周${weekdays[d.getDay()]}`
}

const radarOption = computed(() => {
  if (!report.value?.radar_data) return {}
  const subjects = report.value.radar_data.map(d => d.subject)
  const values = report.value.radar_data.map(d => (d.correct_rate * 100).toFixed(0))
  return {
    tooltip: {
      formatter: (params) => {
        const data = report.value.radar_data[params.dataIndex]
        return `${data.subject}<br/>正确率: ${(data.correct_rate * 100).toFixed(0)}%<br/>做题数: ${data.question_count}`
      },
    },
    legend: { data: ['正确率'], bottom: 0 },
    radar: {
      indicator: subjects.map(s => ({ name: s, max: 100 })),
      center: ['50%', '45%'],
      radius: '65%',
      splitArea: {
        areaStyle: { color: ['rgba(27, 42, 74, 0.02)', 'rgba(27, 42, 74, 0.04)'] },
      },
      splitLine: { lineStyle: { color: 'rgba(27, 42, 74, 0.1)' } },
      axisLine: { lineStyle: { color: 'rgba(27, 42, 74, 0.15)' } },
      axisLabel: { color: '#6B6559' },
      name: { textStyle: { color: '#4A453C', fontSize: 12 } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: values.map(Number),
        name: '正确率',
        areaStyle: { color: 'rgba(217, 119, 6, 0.15)' },
        lineStyle: { color: '#D97706', width: 2 },
        itemStyle: { color: '#D97706' },
      }],
    }],
  }
})
</script>

<style scoped>
.header-actions {
  display: flex;
  gap: 8px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border: none;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-outline {
  background: transparent;
  border: 1.5px solid var(--neutral-300);
  color: var(--neutral-700);
}
.btn-outline:hover:not(:disabled) {
  border-color: var(--ink-700);
  color: var(--ink-700);
  background: var(--ink-50);
}

.btn-accent {
  background: var(--amber-600);
  color: #fff;
}
.btn-accent:hover:not(:disabled) {
  background: #B45309;
  box-shadow: 0 0 20px rgba(217, 119, 6, 0.15);
}

/* ── 总览 ── */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.overview-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  text-align: center;
  transition: box-shadow 0.2s;
}
.overview-card:hover {
  box-shadow: var(--shadow-md);
}
.ov-number {
  font-size: 34px;
  font-weight: 800;
  color: var(--ink-900);
  font-family: var(--font-display);
}
.ov-unit {
  font-size: 18px;
  font-weight: 600;
  color: var(--neutral-500);
  margin-left: 2px;
}
.ov-label {
  font-size: 14px;
  color: var(--neutral-600);
  margin-top: 4px;
  font-weight: 500;
}

/* ── 区块 ── */
.section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 22px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
}
.section h3 {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 700;
  margin: 0 0 16px;
  color: var(--ink-900);
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-icon {
  font-size: 18px;
}

.radar-container {
  width: 100%;
}

.weakness-card {
  background: var(--amber-50);
  border: 1px solid var(--amber-400);
  border-left: 4px solid var(--amber-600);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
  margin-bottom: 10px;
}
.weakness-header {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
}
.subject-tag {
  background: var(--ink-900);
  color: #fff;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
}
.concept {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}
.suggestion {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.summary-section p {
  line-height: 1.9;
  font-size: 14px;
  color: var(--text-primary);
  margin: 0;
}

/* ═══ 历程 ═══ */
.journey-header {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.journey-stat {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 22px;
  text-align: center;
  transition: box-shadow 0.2s;
}
.journey-stat:hover {
  box-shadow: var(--shadow-md);
}
.stat-num {
  font-size: 30px;
  font-weight: 800;
  color: var(--ink-900);
  font-family: var(--font-display);
  display: block;
}
.stat-label {
  font-size: 13px;
  color: var(--neutral-600);
  margin-top: 4px;
  display: block;
  font-weight: 500;
}

.subjects-cloud {
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

.timeline {
  position: relative;
  padding-left: 28px;
}
.empty-timeline {
  text-align: center;
  padding: 40px;
  color: var(--neutral-500);
}

.timeline-item {
  position: relative;
  padding-bottom: 24px;
}
.timeline-dot {
  position: absolute;
  left: -28px;
  top: 4px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--amber-500);
  border: 3px solid var(--surface);
  box-shadow: 0 0 0 2px var(--amber-500);
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
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 18px;
  transition: box-shadow 0.2s;
}
.timeline-card:hover {
  box-shadow: var(--shadow-sm);
}
.timeline-date {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-900);
  margin-bottom: 6px;
}
.timeline-subjects {
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
.timeline-summary {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}
</style>
