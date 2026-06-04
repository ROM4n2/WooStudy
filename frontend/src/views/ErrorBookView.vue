<template>
  <div class="errorbook-view page-ambient fade-in-up">
    <div class="page-header">
      <h2>📝 错题本</h2>
      <div class="filters">
        <select v-model="filterSubject">
          <option value="">全部科目</option>
          <option v-for="s in subjects" :key="s" :value="s">{{ s }}</option>
        </select>
        <select v-model="filterReviewed">
          <option value="">全部状态</option>
          <option value="0">待复习</option>
          <option value="1">已复习</option>
        </select>
      </div>
    </div>

    <!-- 加载 -->
    <div v-if="loading" class="loading-state">加载中...</div>

    <!-- 空状态 -->
    <div v-else-if="total === 0" class="empty-state">
      <div class="empty-icon">🎉</div>
      <p>还没有错题记录，继续保持！</p>
    </div>

    <!-- 分组展示 -->
    <div v-else class="groups">
      <div v-for="(items, subject) in groupedErrors" :key="subject" class="group">
        <h3 class="group-title">{{ subject }} <span class="count">({{ items.length }})</span></h3>
        <div v-for="item in items" :key="item.id" :class="['error-card', { reviewed: item.reviewed }]">
          <div class="card-header">
            <span class="subject-badge">{{ item.subject }}</span>
            <span :class="['status-badge', item.reviewed ? 'reviewed' : 'pending']">
              {{ item.reviewed ? '已复习' : '待复习' }}
            </span>
          </div>

          <div class="card-body">
            <div class="question-text" v-html="renderKaTeX(item.content)"></div>
            <div class="answer-comparison">
              <div class="user-answer">
                <span class="label">你的答案:</span>
                <span class="value wrong" v-html="renderKaTeX(item.user_answer)"></span>
              </div>
              <div class="correct-answer">
                <span class="label">正确答案:</span>
                <span class="value correct" v-html="renderKaTeX(item.correct_answer)"></span>
              </div>
            </div>
            <div v-if="item.wrong_reason" class="wrong-reason">
              <span class="label">错误原因:</span> {{ item.wrong_reason }}
            </div>
            <div v-if="item.explanation" class="explanation" v-html="renderKaTeX(item.explanation)"></div>
          </div>

          <div class="card-actions">
            <button
              :class="['btn', item.reviewed ? 'btn-outline' : 'btn-primary']"
              @click="toggleReview(item)"
            >
              {{ item.reviewed ? '标记未复习' : '标记已复习' }}
            </button>
            <button class="btn btn-outline" @click="handleGenerateVariant(item)" :disabled="item.generating">
              <template v-if="item.generating">⏳ 生成中...</template>
              <template v-else>🎯 生成变式</template>
            </button>
          </div>

          <!-- 变式题列表 -->
          <div v-if="item.variants && item.variants.length > 0" class="variants">
            <h4>变式题 ({{ item.variants.length }})</h4>
            <div v-for="v in item.variants" :key="v.id" class="variant-item">
              <div class="variant-text" v-html="renderKaTeX(v.content)"></div>
              <div v-if="v.options" class="variant-options">
                <div v-for="opt in v.options" :key="opt" class="variant-option" v-html="renderKaTeX(opt)"></div>
              </div>
              <div class="variant-answer">
                <button v-if="!revealedAnswers.has(v.id)" class="btn-ghost-sm" @click="toggleReveal(v.id)">👁 显示答案</button>
                <span v-else>
                  ✅ 答案: <strong v-html="renderKaTeX(v.correct_answer)"></strong>
                  <button class="btn-ghost-sm" @click="toggleReveal(v.id)" style="margin-left:8px">隐藏</button>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { getErrorLogs, markReviewed, generateVariant } from '../api/errorbook'
import { renderKaTeX } from '../utils/katex'
import { SUBJECTS } from '../constants/subjects'

const subjects = SUBJECTS
const errors = ref([])
const loading = ref(true)
const filterSubject = ref('')
const filterReviewed = ref('')
const revealedAnswers = reactive(new Set())

const groupedErrors = computed(() => {
  const groups = {}
  for (const item of errors.value) {
    const key = item.subject || '未分类'
    if (!groups[key]) groups[key] = []
    groups[key].push(item)
  }
  return groups
})

const total = computed(() => errors.value.length)

function toggleReveal(variantId) {
  if (revealedAnswers.has(variantId)) {
    revealedAnswers.delete(variantId)
  } else {
    revealedAnswers.add(variantId)
  }
}

async function loadErrors() {
  loading.value = true
  try {
    const params = { group_by_subject: true }
    if (filterSubject.value) params.subject = filterSubject.value
    if (filterReviewed.value !== '') params.reviewed = filterReviewed.value === '1'
    const res = await getErrorLogs(params)
    const all = []
    for (const [, items] of Object.entries(res.groups || {})) {
      all.push(...items)
    }
    errors.value = all
  } catch {
    errors.value = []
  } finally {
    loading.value = false
  }
}

async function toggleReview(item) {
  try {
    await markReviewed(item.id, !item.reviewed)
    item.reviewed = !item.reviewed
  } catch (e) {
    alert('操作失败: ' + e.message)
  }
}

async function handleGenerateVariant(item) {
  item.generating = true
  try {
    const res = await generateVariant(item.id)
    if (res.variant) {
      if (!item.variants) item.variants = []
      item.variants.push(res.variant)
    }
  } catch (e) {
    alert('生成失败: ' + e.message)
  } finally {
    item.generating = false
  }
}

watch([filterSubject, filterReviewed], loadErrors)
onMounted(loadErrors)
</script>

<style scoped>
.filters { display: flex; gap: 8px; }
.filters select {
  padding: 7px 14px;
  border: 1.5px solid var(--neutral-300);
  border-radius: var(--radius-sm);
  font-size: 13px;
  background: var(--surface);
  color: var(--text-primary);
  cursor: pointer;
  outline: none;
}
.filters select:focus {
  border-color: var(--ink-700);
}

.group { margin-bottom: 28px; }

.group-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 2.5px solid var(--ink-100);
  color: var(--ink-900);
}
.count {
  font-size: 14px;
  color: var(--neutral-500);
  font-weight: 400;
  font-family: var(--font-body);
}

.error-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid var(--rose-500);
  border-radius: var(--radius-lg);
  padding: 18px;
  margin-bottom: 14px;
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.2s, opacity 0.2s;
}
.error-card:hover {
  box-shadow: var(--shadow-md);
}
.error-card.reviewed {
  opacity: 0.7;
  border-left-color: var(--teal-500);
}

.card-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.subject-badge {
  background: var(--ink-50);
  color: var(--ink-700);
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}
.status-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 12px;
}
.status-badge.pending {
  background: var(--amber-100);
  color: var(--amber-600);
}
.status-badge.reviewed {
  background: var(--teal-50);
  color: var(--teal-600);
}

.card-body {
  margin-bottom: 14px;
  line-height: 1.7;
  font-size: 14px;
}

.answer-comparison {
  display: flex;
  gap: 28px;
  margin: 10px 0 6px;
}
.answer-comparison .label {
  font-weight: 600;
  color: var(--neutral-500);
  font-size: 13px;
  margin-right: 4px;
}
.value.wrong {
  color: var(--rose-600);
  font-weight: 600;
}
.value.correct {
  color: var(--teal-600);
  font-weight: 600;
}

.wrong-reason {
  margin-top: 8px;
  color: var(--text-secondary);
  font-size: 13px;
}

.explanation {
  margin-top: 10px;
  padding: 12px 14px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  line-height: 1.7;
  font-size: 13px;
  color: var(--text-secondary);
}

.card-actions {
  display: flex;
  gap: 8px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 18px;
  border: none;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--ink-900);
  color: #fff;
}
.btn-primary:hover:not(:disabled) {
  background: var(--ink-800);
}

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

/* ── 变式题 ── */
.variants {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
}
.variants h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.variant-item {
  background: var(--bg-elevated);
  padding: 14px;
  border-radius: var(--radius-sm);
  margin-bottom: 10px;
  line-height: 1.6;
  font-size: 13px;
}
.variant-options {
  margin: 6px 0;
}
.variant-option {
  padding: 2px 0;
}
.variant-answer {
  margin-top: 8px;
  color: var(--teal-600);
  font-weight: 600;
  font-size: 13px;
}

.btn-ghost-sm {
  background: none;
  border: 1px dashed var(--neutral-300);
  color: var(--ink-700);
  cursor: pointer;
  font-size: 12px;
  padding: 3px 12px;
  border-radius: var(--radius-sm);
  transition: all 0.15s;
}
.btn-ghost-sm:hover {
  background: var(--ink-50);
  border-color: var(--ink-700);
}
</style>
