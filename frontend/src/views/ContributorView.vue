<template>
  <div class="contributor-view page-ambient fade-in-up">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>🧠 知识点贡献</h2>
      <div v-if="authStore.isLoggedIn" class="header-actions">
        <span class="user-badge">{{ authStore.user?.username }}</span>
        <span v-if="isAdmin" class="admin-badge">管理员</span>
      </div>
    </div>

    <!-- Tab 导航 -->
    <div class="tab-nav">
      <button
        v-for="t in tabs"
        :key="t.key"
        :class="['tab-item', { active: activeTab === t.key }]"
        @click="activeTab = t.key"
        v-show="!t.adminOnly || isAdmin"
      >
        <span class="tab-icon">{{ t.icon }}</span>
        <span class="tab-label">{{ t.label }}</span>
      </button>
    </div>

    <!-- ═════════ 提价页 ═════════ -->
    <div v-if="activeTab === 'submit'" class="tab-content">
      <div class="submit-card">
        <div class="submit-intro">
          <p class="intro-text">补充你学到的物理知识点，让你的发现成为知识图谱中的一颗新星 ✨</p>
          <p class="intro-hint">提交后由管理员审核，审核通过后即可在知识图谱中看到</p>
        </div>

        <form class="contribute-form" @submit.prevent="handleSubmit">
          <!-- 第一行：学科 + 类型 -->
          <div class="form-row">
            <div class="field half">
              <label class="field-label">学科 <span class="required">*</span></label>
              <div class="select-wrap">
                <select v-model="form.subject" required>
                  <option value="" disabled>选择学科</option>
                  <option v-for="s in SUBJECTS" :key="s" :value="s">{{ s }}</option>
                </select>
              </div>
            </div>
            <div class="field half">
              <label class="field-label">类型 <span class="required">*</span></label>
              <div class="select-wrap">
                <select v-model="form.category" required>
                  <option value="topic">📌 知识点</option>
                  <option value="section">📂 节</option>
                  <option value="chapter">📚 章</option>
                </select>
              </div>
            </div>
          </div>

          <!-- 名称 -->
          <div class="field">
            <label class="field-label">知识点名称 <span class="required">*</span></label>
            <input
              v-model="form.label"
              class="field-input"
              placeholder="例：牛顿第一定律、电场强度"
              required
              @input="autoGenerateId"
            />
          </div>

          <!-- 标识 -->
          <div class="field">
            <label class="field-label">
              英文标识
              <span class="field-hint-inline">自动生成，可手动修改</span>
            </label>
            <div class="id-input-wrap">
              <span class="id-prefix">id:</span>
              <input
                v-model="form.id"
                class="field-input id-input"
                placeholder="newton_first_law"
              />
              <button type="button" class="id-regenerate" @click="autoGenerateId" title="重新生成">🔄</button>
            </div>
          </div>

          <!-- 描述 -->
          <div class="field">
            <label class="field-label">描述</label>
            <textarea
              v-model="form.description"
              class="field-textarea"
              placeholder="简要描述这个知识点的核心内容..."
              rows="3"
            ></textarea>
          </div>

          <!-- 父知识点 -->
          <div class="field">
            <label class="field-label">父知识点 <span class="optional">（可选）</span></label>
            <div class="select-wrap">
              <select v-model="form.parent_id">
                <option value="">无（作为顶级节点）</option>
                <optgroup v-for="(nodes, subj) in approvedBySubject" :key="subj" :label="subj">
                  <option v-for="n in nodes" :key="n.id" :value="n.id">
                    {{ '  '.repeat(categoryLevel(n.category)) }}{{ n.label }}
                  </option>
                </optgroup>
              </select>
            </div>
          </div>

          <!-- 重要度 -->
          <div class="field">
            <label class="field-label">重要度</label>
            <div class="star-rating">
              <button
                v-for="i in 5"
                :key="i"
                type="button"
                :class="['star-btn', { active: i <= form.importance }]"
                @click="form.importance = i"
                :title="i + ' 星'"
              >
                <svg width="22" height="22" viewBox="0 0 24 24" :fill="i <= form.importance ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="1.5">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </button>
              <span class="star-label">{{ ['', '⭐ 基础', '⭐⭐ 了解', '⭐⭐⭐ 重要', '⭐⭐⭐⭐ 重点', '⭐⭐⭐⭐⭐ 核心'][form.importance] }}</span>
            </div>
          </div>

          <!-- 提交 -->
          <div class="form-actions">
            <p v-if="submitMsg" :class="['submit-msg', submitOk ? 'success' : 'error']">
              {{ submitMsg }}
            </p>
            <button type="submit" class="btn btn-accent btn-lg submit-btn" :disabled="submitting">
              <template v-if="submitting">
                <span class="dots-loader"><span></span><span></span><span></span></span> 提交中...
              </template>
              <template v-else>
                🚀 提交贡献
              </template>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ═════════ 我的贡献 ═════════ -->
    <div v-if="activeTab === 'mine'" class="tab-content">
      <div v-if="loadingMine" class="loading-state"><div class="spinner"></div>加载中...</div>
      <div v-else-if="myContributions.length === 0" class="empty-state">
        <div class="empty-icon">🌱</div>
        <p class="empty-title">还没有贡献过知识点</p>
        <p class="empty-hint">点击"提交贡献"开始补充你的物理知识！</p>
        <button class="btn btn-accent" @click="activeTab = 'submit'">去贡献 →</button>
      </div>
      <div v-else class="contribution-list">
        <div
          v-for="item in myContributions"
          :key="item.id"
          class="contribution-card"
        >
          <div class="contrib-header">
            <span class="contrib-label">{{ item.label }}</span>
            <span :class="['status-tag', item.status]">
              {{ statusLabel(item.status) }}
            </span>
          </div>
          <div class="contrib-meta">
            <span class="meta-subject">{{ item.subject }}</span>
            <span class="meta-category">{{ categoryLabel(item.category) }}</span>
            <span v-if="item.description" class="meta-desc">{{ item.description }}</span>
          </div>
          <div class="contrib-id">
            <code>{{ item.id }}</code>
          </div>
          <div v-if="item.status === 'rejected'" class="contrib-rejected-note">
            💡 如想修改后重新提交，可以新建一个贡献
          </div>
        </div>
      </div>
    </div>

    <!-- ═════════ 审核管理（管理员） ═════════ -->
    <div v-if="activeTab === 'review'" class="tab-content">
      <div class="review-intro">
        <h3>📋 待审核知识点（{{ pendingItems.length }} 项）</h3>
      </div>
      <div v-if="loadingPending" class="loading-state"><div class="spinner spinner-accent"></div>加载中...</div>
      <div v-else-if="pendingItems.length === 0" class="empty-state">
        <div class="empty-icon">✅</div>
        <p class="empty-title">没有待审核的知识点</p>
        <p class="empty-hint">所有贡献都已处理完毕</p>
      </div>
      <div v-else class="pending-list">
        <div
          v-for="item in pendingItems"
          :key="item.id"
          class="pending-card"
        >
          <div class="pending-header">
            <span class="pending-label">{{ item.label }}</span>
            <span class="pending-id"><code>{{ item.id }}</code></span>
          </div>
          <div class="pending-meta">
            <span class="tag tag-ink">{{ item.subject }}</span>
            <span class="tag tag-teal">{{ categoryLabel(item.category) }}</span>
            <span v-if="item.description" class="pending-desc">{{ item.description }}</span>
          </div>
          <div class="pending-actions">
            <button class="btn btn-sm btn-primary" @click="handleApprove(item.id)">
              ✅ 批准
            </button>
            <button class="btn btn-sm btn-danger" @click="handleReject(item.id)">
              ❌ 拒绝
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { SUBJECTS } from '../constants/subjects'
import {
  submitContribution,
  getPendingContributions,
  approveContribution,
  rejectContribution,
  getKnowledgeGraph,
} from '../api/knowledge'

const authStore = useAuthStore()

const isAdmin = computed(() => authStore.user?.role === 'admin')

const tabs = [
  { key: 'submit', icon: '✍️', label: '提交贡献' },
  { key: 'mine', icon: '📋', label: '我的贡献' },
  { key: 'review', icon: '✅', label: '审核管理', adminOnly: true },
]
const activeTab = ref('submit')

// ── 提价表单 ──
const form = reactive({
  subject: '',
  category: 'topic',
  label: '',
  id: '',
  description: '',
  parent_id: '',
  importance: 3,
})
const submitting = ref(false)
const submitMsg = ref('')
const submitOk = ref(false)

// ── 已 approved 的知识点（供父节点选择） ──
const approvedNodes = ref([])
const approvedBySubject = computed(() => {
  const grouped = {}
  for (const n of approvedNodes.value) {
    if (!grouped[n.subject]) grouped[n.subject] = []
    grouped[n.subject].push(n)
  }
  return grouped
})

function categoryLevel(cat) {
  return { chapter: 0, section: 1, topic: 2 }[cat] || 0
}

function autoGenerateId() {
  if (!form.label) return
  // 中文拼音化简化：取前三个中文字符的拼音首字母
  const cleaned = form.label
    .replace(/[（(].*[）)]/g, '')
    .replace(/[·•]/g, '_')
    .trim()
  // 用简单规则：中文转小写字母+下划线
  const id = cleaned
    .toLowerCase()
    .replace(/\s+/g, '_')
    .replace(/[^a-z0-9_一-鿿]/g, '')
    .replace(/[一-鿿]/g, match => {
      // 简单映射几个常见字
      const map = { '牛': 'niu', '顿': 'dun', '第': 'di', '一': 'yi', '定': 'ding', '律': 'lv',
        '电': 'dian', '场': 'chang', '强': 'qiang', '度': 'du', '磁': 'ci', '感': 'gan', '应': 'ying',
        '力': 'li', '学': 'xue', '热': 're', '光': 'guang', '近': 'jin', '代': 'dai', '物': 'wu',
        '理': 'li', '原': 'yuan', '子': 'zi', '核': 'he', '能': 'neng', '量': 'liang',
        '守': 'shou', '恒': 'heng', '动': 'dong', '速': 'su', '加': 'jia', '位': 'wei',
        '移': 'yi', '路': 'lu', '程': 'cheng', '公': 'gong', '式': 'shi', '法': 'fa',
        '欧': 'ou', '姆': 'mu', '电': 'dian', '阻': 'zu', '功': 'gong', '率': 'lv',
        '周': 'zhou', '期': 'qi', '频': 'pin', '振': 'zhen', '幅': 'fu',
        '弹': 'tan', '摩': 'mo', '擦': 'ca', '重': 'zhong', '力': 'li',
        '分': 'fen', '解': 'jie', '合': 'he', '成': 'cheng', '正': 'zheng',
        '交': 'jiao', '直': 'zhi', '流': 'liu', '电': 'dian', '压': 'ya' }
      return map[match] || match
    })
    .replace(/[一-鿿]/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '')
    .substring(0, 40)
  form.id = id || 'new_topic'
}

// ── 我的贡献 ──
const myContributions = ref([])
const loadingMine = ref(false)

// ── 审核 ──
const pendingItems = ref([])
const loadingPending = ref(false)

onMounted(async () => {
  await loadApprovedNodes()
  await loadMyContributions()
  if (isAdmin.value) await loadPending()
})

async function loadApprovedNodes() {
  try {
    const res = await getKnowledgeGraph()
    approvedNodes.value = res.nodes || []
  } catch { /* 静默 */ }
}

async function loadMyContributions() {
  loadingMine.value = true
  try {
    const res = await getKnowledgeGraph()
    // 从所有节点中过滤出该用户的贡献
    const all = res.nodes || []
    // 贡献的节点是 source='user' 或 id 以 'contrib_' 开头的
    myContributions.value = all.filter(n => n.id.startsWith('contrib_') || n.source === 'user')
  } catch {
    myContributions.value = []
  } finally {
    loadingMine.value = false
  }
}

async function loadPending() {
  loadingPending.value = true
  try {
    const res = await getPendingContributions()
    pendingItems.value = res.items || []
  } catch {
    pendingItems.value = []
  } finally {
    loadingPending.value = false
  }
}

async function handleSubmit() {
  if (!form.label || !form.subject) return
  submitting.value = true
  submitMsg.value = ''
  submitOk.value = false
  try {
    const data = { ...form }
    await submitContribution(data)
    submitMsg.value = '✅ 提交成功！知识点已进入审核流程，管理员审核后即可上线。'
    submitOk.value = true
    // 重置表单
    form.subject = ''
    form.category = 'topic'
    form.label = ''
    form.id = ''
    form.description = ''
    form.parent_id = ''
    form.importance = 3
    await loadMyContributions()
  } catch (e) {
    submitMsg.value = '❌ ' + (e.message || '提交失败，请重试')
    submitOk.value = false
  } finally {
    submitting.value = false
  }
}

async function handleApprove(nodeId) {
  try {
    await approveContribution(nodeId)
    pendingItems.value = pendingItems.value.filter(i => i.id !== nodeId)
    await loadApprovedNodes()
  } catch (e) {
    alert('操作失败: ' + e.message)
  }
}

async function handleReject(nodeId) {
  if (!confirm('确定拒绝此贡献？')) return
  try {
    await rejectContribution(nodeId)
    pendingItems.value = pendingItems.value.filter(i => i.id !== nodeId)
  } catch (e) {
    alert('操作失败: ' + e.message)
  }
}

function statusLabel(status) {
  return { pending: '⏳ 待审核', approved: '✅ 已通过', rejected: '❌ 已拒绝' }[status] || status
}

function categoryLabel(cat) {
  return { chapter: '章', section: '节', topic: '知识点' }[cat] || cat
}
</script>

<style scoped>
/* ══ Tab 导航（胶囊风格） ══ */
.tab-nav {
  display: flex;
  gap: 4px;
  margin-bottom: 28px;
  padding: 4px;
  border-radius: var(--radius);
  background: var(--neutral-100);
}
.tab-item {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 18px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  color: var(--neutral-500);
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out-soft);
}
.tab-item:hover { color: var(--neutral-700); }
.tab-item.active {
  background: var(--surface);
  color: var(--ink-900);
  font-weight: 600;
  box-shadow: var(--shadow-xs);
}
.tab-icon { font-size: 14px; line-height: 1; }
.tab-label { line-height: 1; }

/* ══ 提价卡片 ══ */
.submit-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 32px;
  box-shadow: var(--shadow-sm);
  animation: fadeInUp 0.4s var(--ease-out-soft);
}

.submit-intro {
  text-align: center;
  margin-bottom: 28px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border);
}
.intro-text {
  font-size: 15px;
  color: var(--text-primary);
  font-weight: 500;
  margin: 0 0 6px;
}
.intro-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
}

/* ══ 表单项 ══ */
.contribute-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 640px;
  margin: 0 auto;
}
.form-row {
  display: flex;
  gap: 16px;
}
.half { flex: 1; }

.field { display: flex; flex-direction: column; gap: 6px; }
.field-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--neutral-700);
}
.required { color: var(--rose-500); }
.optional { color: var(--neutral-400); font-weight: 400; font-size: 12px; }
.field-hint-inline { color: var(--neutral-400); font-weight: 400; font-size: 12px; margin-left: 8px; }

.field-input, .field-textarea, .select-wrap select {
  width: 100%;
  padding: 10px 14px;
  border: 1.5px solid var(--neutral-300);
  border-radius: var(--radius);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--text-primary);
  outline: none;
  background: var(--bg-elevated);
  transition: all var(--duration-normal) var(--ease-out-soft);
  box-sizing: border-box;
}
.field-input:focus, .field-textarea:focus, .select-wrap select:focus {
  border-color: var(--amber-500);
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.08);
}
.field-textarea {
  resize: vertical;
  min-height: 72px;
  line-height: 1.6;
}

.select-wrap { position: relative; }
.select-wrap select {
  appearance: none;
  -webkit-appearance: none;
  cursor: pointer;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' fill='%236B6559'%3E%3Cpath d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 36px;
}

/* ══ ID 输入行 ══ */
.id-input-wrap {
  display: flex;
  align-items: center;
  gap: 0;
  border: 1.5px solid var(--neutral-300);
  border-radius: var(--radius);
  background: var(--bg-elevated);
  transition: all var(--duration-normal) var(--ease-out-soft);
}
.id-input-wrap:focus-within {
  border-color: var(--amber-500);
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.08);
}
.id-prefix {
  padding: 0 0 0 14px;
  color: var(--neutral-400);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 500;
}
.id-input {
  border: none !important;
  box-shadow: none !important;
  flex: 1;
  background: transparent !important;
  font-family: var(--font-mono) !important;
  letter-spacing: 0.02em;
}
.id-input-wrap:focus-within .id-input:focus {
  box-shadow: none !important;
}
.id-regenerate {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px 12px;
  color: var(--neutral-400);
  font-size: 14px;
  transition: all var(--duration-fast);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}
.id-regenerate:hover {
  color: var(--ink-700);
  background: var(--ink-50);
}

/* ══ 星级 ══ */
.star-rating {
  display: flex;
  align-items: center;
  gap: 4px;
}
.star-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: var(--neutral-300);
  transition: all var(--duration-fast) var(--ease-out-soft);
  line-height: 1;
}
.star-btn:hover {
  transform: scale(1.15);
}
.star-btn.active {
  color: var(--amber-500);
}
.star-btn:hover ~ .star-btn {
  color: var(--neutral-300);
}
.star-rating:hover .star-btn {
  color: var(--amber-300);
}
.star-rating:hover .star-btn:hover {
  color: var(--amber-500);
  transform: scale(1.2);
}
.star-rating:hover .star-btn:hover ~ .star-btn {
  color: var(--neutral-300);
}
.star-label {
  margin-left: 12px;
  font-size: 13px;
  color: var(--neutral-500);
  font-weight: 500;
}

/* ══ 提交按钮 ══ */
.form-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
  margin-top: 8px;
}
.submit-btn {
  width: 100%;
  justify-content: center;
  padding: 12px 32px;
  font-size: 15px;
}
.submit-msg {
  font-size: 14px;
  font-weight: 500;
  text-align: center;
  margin: 0;
  padding: 10px 16px;
  border-radius: var(--radius);
  width: 100%;
  animation: scaleIn 0.3s var(--ease-spring);
}
.submit-msg.success {
  background: var(--teal-50);
  color: var(--teal-600);
  border: 1px solid var(--teal-100);
}
.submit-msg.error {
  background: var(--rose-50);
  color: var(--rose-600);
  border: 1px solid var(--rose-100);
}

/* ══ 我的贡献列表 ══ */
.contribution-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.contribution-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  box-shadow: var(--shadow-sm);
  transition: all var(--duration-normal) var(--ease-out-soft);
  animation: fadeInUp 0.35s var(--ease-out-soft);
}
.contribution-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}
.contrib-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.contrib-label {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--ink-900);
}
.status-tag {
  font-size: 12px;
  font-weight: 600;
  padding: 3px 12px;
  border-radius: var(--radius-full);
}
.status-tag.pending { background: var(--amber-100); color: var(--amber-700); }
.status-tag.approved { background: var(--teal-100); color: var(--teal-600); }
.status-tag.rejected { background: var(--rose-100); color: var(--rose-600); }

.contrib-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  font-size: 13px;
  color: var(--neutral-500);
  margin-bottom: 6px;
}
.meta-subject {
  background: var(--ink-50);
  color: var(--ink-700);
  padding: 1px 8px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 600;
}
.meta-category {
  font-size: 12px;
  color: var(--neutral-400);
}
.meta-desc {
  color: var(--neutral-500);
  font-size: 13px;
  width: 100%;
  margin-top: 4px;
}
.contrib-id code {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--neutral-400);
  background: var(--neutral-100);
  padding: 2px 6px;
  border-radius: var(--radius-xs);
}
.contrib-rejected-note {
  margin-top: 10px;
  font-size: 13px;
  color: var(--neutral-500);
  padding: 8px 12px;
  background: var(--bg-elevated);
  border-radius: var(--radius);
}

/* ══ 审核管理 ══ */
.review-intro {
  margin-bottom: 20px;
}
.review-intro h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: var(--ink-900);
}

.pending-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.pending-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid var(--amber-500);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  box-shadow: var(--shadow-sm);
  transition: all var(--duration-normal) var(--ease-out-soft);
  animation: fadeInUp 0.35s var(--ease-out-soft);
}
.pending-card:hover {
  box-shadow: var(--shadow-md);
}
.pending-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.pending-label {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--ink-900);
}
.pending-id code {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--neutral-400);
}
.pending-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.pending-desc {
  width: 100%;
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 6px;
}
.pending-actions {
  display: flex;
  gap: 8px;
}

/* ══ 头部用户标识 ══ */
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-badge {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-900);
}
.admin-badge {
  font-size: 11px;
  font-weight: 700;
  color: var(--amber-700);
  background: var(--amber-100);
  padding: 2px 10px;
  border-radius: var(--radius-full);
}

/* ══ 响应式 ══ */
@media (max-width: 768px) {
  .submit-card { padding: 20px 16px; }
  .form-row { flex-direction: column; gap: 16px; }
  .tab-item { padding: 8px 12px; font-size: 12px; }
  .contribute-form { max-width: 100%; }
}
</style>
