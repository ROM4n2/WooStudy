<template>
  <div class="practice-view">
    <div class="page-header">
      <h2>✏️ 智能刷题</h2>
      <div class="controls">
        <select v-model="subject">
          <option value="">全部科目</option>
          <option v-for="s in subjects" :key="s" :value="s">{{ s }}</option>
        </select>
        <select v-model="difficulty">
          <option value="">全部难度</option>
          <option :value="1">⭐ 简单</option>
          <option :value="2">⭐⭐ 较易</option>
          <option :value="3">⭐⭐⭐ 中等</option>
          <option :value="4">⭐⭐⭐⭐ 较难</option>
          <option :value="5">⭐⭐⭐⭐⭐ 困难</option>
        </select>
        <button class="btn btn-accent" @click="loadQuestions" :disabled="loading">
          {{ loading ? '加载中...' : '开始刷题' }}
        </button>
      </div>
    </div>

    <!-- 薄弱科目推荐 -->
    <div v-if="weakSubjects.length > 0 && !loading" class="weak-banner">
      📌 根据你的错题数据，推荐优先巩固：
      <strong v-for="(s, i) in weakSubjects" :key="s">
        {{ s }}{{ i < weakSubjects.length - 1 ? '、' : '' }}
      </strong>
    </div>

    <!-- 答题进度 -->
    <div v-if="questions.length > 0" class="progress-bar-wrapper">
      <div class="progress-info">
        <span>答题进度</span>
        <span>{{ answeredCount }}/{{ questions.length }} 题 · 正确率 {{ correctRate }}%</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="questions.length === 0 && !loading" class="empty-state">
      <div class="empty-icon">📚</div>
      <p class="empty-title">点击"开始刷题"获取推荐题目</p>
      <p class="empty-hint" v-if="weakSubjects.length > 0">系统会根据你的错题记录优先推荐薄弱科目</p>
    </div>

    <!-- 题目列表 -->
    <div v-for="(q, idx) in questions" :key="q.id" class="question-card">
      <div class="q-header">
        <span class="q-number">第 {{ idx + 1 }} 题</span>
        <span class="q-tag">{{ q.subject }}</span>
        <span class="q-difficulty">{{ '⭐'.repeat(q.difficulty) }}</span>
        <span v-if="q._result" :class="['q-result-tag', q._result.is_correct ? 'correct' : 'wrong']">
          {{ q._result.is_correct ? '✓ 正确' : '✗ 错误' }}
        </span>
      </div>

      <div class="q-content" v-html="renderKaTeX(q.content)"></div>

      <div v-if="q.options" class="q-options">
        <div
          v-for="opt in q.options"
          :key="opt"
          :class="['option', {
            selected: answers[q.id] === opt.charAt(0),
            correct: q._result && opt.charAt(0) === q._result.correct_answer,
            wrong: q._result && answers[q.id] === opt.charAt(0) && opt.charAt(0) !== q._result.correct_answer,
            disabled: q._result,
          }]"
          @click="selectAnswer(q.id, opt.charAt(0))"
        >
          <span v-html="renderKaTeX(opt)"></span>
        </div>
      </div>

      <div v-else class="q-fill">
        <input
          v-model="answers[q.id]"
          placeholder="输入你的答案..."
          :disabled="!!q._result"
        />
      </div>

      <div v-if="!q._result" class="q-actions">
        <button class="btn btn-primary" @click="handleSubmitAnswer(q)" :disabled="!answers[q.id]">
          提交
        </button>
      </div>

      <div v-if="q._result" class="result-block">
        <div :class="['result-banner', q._result.is_correct ? 'correct' : 'wrong']">
          <span class="result-icon">{{ q._result.is_correct ? '✅' : '❌' }}</span>
          <span v-if="!q._result.is_correct">
            正确答案：<strong>{{ q._result.correct_answer }}</strong>
          </span>
          <span v-else>回答正确！</span>
        </div>
        <div v-if="q._result.explanation" class="explanation" v-html="renderKaTeX(q._result.explanation)"></div>
        <div v-if="!q._result.is_correct" class="errorbook-hint">
          ⚡ 已收入错题本，可在错题本中查看变式题
        </div>
      </div>
    </div>

    <!-- 底部操作 -->
    <div v-if="questions.length > 0" class="bottom-actions">
      <div class="session-summary">
        本次共答 <strong>{{ answeredCount }}</strong> 题，正确 <strong>{{ correctCount }}</strong> 题
        （正确率 <strong>{{ correctRate }}%</strong>）
        <span v-if="answeredCount === questions.length" class="complete-badge">🎉 本组完成</span>
      </div>
      <button class="btn btn-outline" @click="loadQuestions" :disabled="loading">
        🔄 再来一组
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { getQuestions, submitAnswer } from '../api/practice'
import { renderKaTeX } from '../utils/katex'
import { SUBJECTS } from '../constants/subjects'

const subjects = SUBJECTS
const questions = ref([])
const answers = reactive({})
const loading = ref(false)
const weakSubjects = ref([])
const subject = ref('')
const difficulty = ref('')

const answeredCount = computed(() => questions.value.filter(q => q._result).length)
const correctCount = computed(() => questions.value.filter(q => q._result?.is_correct).length)
const correctRate = computed(() => {
  if (answeredCount.value === 0) return 0
  return Math.round((correctCount.value / answeredCount.value) * 100)
})
const progressPercent = computed(() => {
  if (questions.value.length === 0) return 0
  return (answeredCount.value / questions.value.length) * 100
})

async function loadQuestions() {
  loading.value = true
  try {
    const params = { count: 5 }
    if (subject.value) params.subject = subject.value
    if (difficulty.value) params.difficulty = Number(difficulty.value)
    const res = await getQuestions(params)
    questions.value = (res.questions || []).map(q => ({ ...q, _result: null }))
    weakSubjects.value = res.weak_subjects || []
    Object.keys(answers).forEach(k => delete answers[k])
  } catch (e) {
    alert('获取题目失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

function selectAnswer(qId, choice) {
  const q = questions.value.find(x => x.id === qId)
  if (q?._result) return
  answers[qId] = choice
}

async function handleSubmitAnswer(q) {
  if (!answers[q.id]) return
  try {
    const res = await submitAnswer(q.id, answers[q.id])
    q._result = res
  } catch (e) {
    alert('提交失败: ' + e.message)
  }
}
</script>

<style scoped>
/* ══ 控制区 ══ */
.controls {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

/* ══ 薄弱科目 Banner ══ */
.weak-banner {
  background: linear-gradient(135deg, var(--amber-50) 0%, var(--bg-elevated) 100%);
  border: 1px solid var(--amber-200);
  border-left: 4px solid var(--amber-600);
  border-radius: var(--radius);
  padding: 12px 18px;
  font-size: 13px;
  color: #92400E;
  margin-bottom: 20px;
  line-height: 1.6;
  animation: slideUp 0.35s var(--ease-out-soft);
}

/* ══ 进度条（动态渐变） ══ */
.progress-bar-wrapper {
  margin-bottom: 20px;
  animation: fadeInDown 0.3s var(--ease-out-soft);
}
.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--neutral-600);
  margin-bottom: 6px;
}
.progress-track {
  height: 6px;
  background: var(--neutral-200);
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--teal-600), var(--teal-400));
  border-radius: 3px;
  transition: width 0.5s var(--ease-out-soft);
  position: relative;
}
.progress-fill::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  animation: shimmerProgress 2s ease-in-out infinite;
}
@keyframes shimmerProgress {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* ══ 题目卡片 ══ */
.question-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid var(--ink-500);
  border-radius: var(--radius-lg);
  padding: 22px;
  margin-bottom: 18px;
  box-shadow: var(--shadow-sm);
  transition: all var(--duration-normal) var(--ease-out-soft);
  animation: fadeInUp 0.35s var(--ease-out-soft);
}
.question-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.q-header {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.q-number {
  font-weight: 700;
  color: var(--ink-700);
  font-size: 14px;
}
.q-tag {
  background: var(--ink-50);
  color: var(--ink-700);
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 600;
}
.q-difficulty {
  font-size: 13px;
  color: var(--neutral-500);
}
.q-result-tag {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  margin-left: auto;
}
.q-result-tag.correct { background: var(--teal-50); color: var(--teal-600); }
.q-result-tag.wrong { background: var(--rose-50); color: var(--rose-600); }

.q-content {
  line-height: 1.9;
  font-size: 15px;
  margin-bottom: 18px;
  color: var(--text-primary);
}
.q-content :deep(.formula) { overflow-x: auto; padding: 4px 0; }

/* ══ 选项（增强 hover 微交互） ══ */
.q-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}
.option {
  padding: 12px 18px;
  border: 2px solid var(--neutral-200);
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 14px;
  transition: all var(--duration-normal) var(--ease-out-soft);
  background: var(--bg-elevated);
  position: relative;
}
.option:hover:not(.disabled) {
  border-color: var(--ink-500);
  background: var(--ink-50);
  transform: translateX(3px);
}
.option.selected {
  border-color: var(--ink-700);
  background: var(--ink-50);
  box-shadow: 0 0 0 3px rgba(27, 42, 74, 0.06);
}
.option.correct {
  border-color: var(--teal-600);
  background: var(--teal-50);
  cursor: default;
}
.option.wrong {
  border-color: var(--rose-600);
  background: var(--rose-50);
  cursor: default;
}
.option.disabled { cursor: default; opacity: 0.7; }

.q-fill { margin-bottom: 16px; }
.q-fill input {
  width: 100%;
  padding: 11px 16px;
  border: 2px solid var(--neutral-200);
  border-radius: var(--radius);
  font-size: 14px;
  box-sizing: border-box;
  background: var(--bg-elevated);
  outline: none;
  transition: all var(--duration-normal) var(--ease-out-soft);
}
.q-fill input:focus {
  border-color: var(--ink-700);
  box-shadow: 0 0 0 3px rgba(27, 42, 74, 0.06);
}
.q-actions { margin-bottom: 8px; }

/* ══ 结果区块 ══ */
.result-block {
  margin-top: 14px;
  animation: fadeIn 0.3s var(--ease-out-soft);
}
.result-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 600;
}
.result-banner.correct { background: var(--teal-50); color: var(--teal-600); }
.result-banner.wrong { background: var(--rose-50); color: var(--rose-600); }
.result-icon { font-size: 20px; }

.explanation {
  margin-top: 10px;
  padding: 16px;
  background: var(--bg-elevated);
  border-radius: var(--radius);
  line-height: 1.8;
  font-size: 14px;
  color: var(--text-secondary);
  border: 1px solid var(--border);
}
.errorbook-hint {
  margin-top: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--amber-600);
}

/* ══ 底部 ══ */
.bottom-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 0;
  gap: 12px;
  border-top: 1px solid var(--border);
  margin-top: 8px;
}
.session-summary {
  font-size: 14px;
  color: var(--neutral-600);
}
.complete-badge {
  margin-left: 10px;
  font-size: 13px;
  color: var(--teal-600);
  font-weight: 600;
}
</style>
