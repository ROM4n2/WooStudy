<template>
  <div class="chat-view">
    <div class="chat-header">
      <h2>💬 答疑</h2>
      <div class="header-toggles">
        <label class="toggle" title="开启后每次追问自动总结上下文，AI 能记住之前聊了什么">
          <input type="checkbox" v-model="followUpMode" />
          <span class="toggle-label">追问</span>
        </label>
        <label class="toggle" title="开启后使用 DeepSeek 深度推理">
          <input type="checkbox" :checked="userStore.deepMode" @change="userStore.toggleDeepMode()" />
          <span class="toggle-label">深度</span>
        </label>
      </div>
    </div>

    <!-- 对话区域 -->
    <div class="messages" ref="messagesRef">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">🤔</div>
        <p class="empty-title">有什么物理问题？</p>
        <p class="empty-hint">可以文字提问，也可以拍照上传题目</p>
      </div>

      <div
        v-for="msg in messages"
        :key="msg.id"
        :class="['message', msg.role === 'user' ? 'user-msg' : 'ai-msg']"
      >
        <div class="msg-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
        <div class="msg-content">
          <img v-if="msg.image_url" :src="msg.image_url" class="msg-image" alt="题目图片" />
          <div class="msg-text" v-html="renderMarkdown(msg.content)"></div>
          <div v-if="msg.model_used" class="msg-meta">{{ msg.model_used }}</div>
        </div>
        <!-- Combo 连击标记 -->
        <div
          v-if="msg.role === 'user' && msg._combo"
          :class="['combo-tag', { 'combo-enter': msg._combo > 0 }]"
        >
          🔥 ×{{ msg._combo }}
        </div>
      </div>

      <!-- 加载动画 -->
      <div v-if="loading" class="message ai-msg">
        <div class="msg-avatar">🤖</div>
        <div class="msg-content">
          <div class="typing-indicator"><span></span><span></span><span></span></div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <div v-if="previewImages.length > 0" class="image-previews">
        <div v-for="(img, idx) in previewImages" :key="idx" class="preview-item">
          <img :src="img.url" alt="upload preview" />
          <button class="remove-img" @click="removeImage(idx)" aria-label="移除图片">✕</button>
        </div>
      </div>

      <div class="input-row">
        <button class="tool-btn" @click="triggerUpload" title="上传图片（最多2张）">📷</button>
        <input
          ref="fileInput"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          hidden
          @change="handleFileSelect"
        />
        <textarea
          v-model="inputText"
          placeholder="输入物理问题... (Enter 发送, Shift+Enter 换行)"
          @keydown.enter.exact="handleSend"
          rows="1"
        ></textarea>
        <button
          v-if="!optimizing"
          class="tool-btn optimize-btn"
          @click="handleOptimize"
          :disabled="!inputText.trim() || loading"
          title="优化提问"
        >
          ✨
        </button>
        <div v-else class="tool-btn optimizing-spinner">⏳</div>
        <button
          class="send-btn"
          @click="handleSend"
          :disabled="loading || (!inputText.trim() && previewImages.length === 0)"
        >
          发送
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useUserStore } from '../stores/user'
import { sendMessage, uploadImage, getHistory, optimizePrompt } from '../api/chat'
import { compressImage } from '../utils/compress'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const userStore = useUserStore()
const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const optimizing = ref(false)
const followUpMode = ref(false)
const comboCount = ref(0)
const fileInput = ref(null)
const messagesRef = ref(null)
const previewImages = ref([])

onMounted(async () => {
  await userStore.loadSettings()
  try {
    const res = await getHistory()
    messages.value = res.messages || []
  } catch { /* 静默 */ }
})

function triggerUpload() { fileInput.value?.click() }

async function handleFileSelect(e) {
  const files = Array.from(e.target.files)
  const remaining = 2 - previewImages.value.length
  for (const file of files.slice(0, remaining)) {
    try {
      const compressed = await compressImage(file)
      previewImages.value.push({ file: compressed, url: URL.createObjectURL(compressed) })
    } catch {
      previewImages.value.push({ file, url: URL.createObjectURL(file) })
    }
  }
  if (files.length > remaining) alert('一次最多上传 2 张图片')
  e.target.value = ''
}

function removeImage(idx) {
  URL.revokeObjectURL(previewImages.value[idx].url)
  previewImages.value.splice(idx, 1)
}

async function handleOptimize() {
  const text = inputText.value.trim()
  if (!text || optimizing.value) return
  optimizing.value = true
  try {
    const res = await optimizePrompt(text)
    inputText.value = res.content || text
    await nextTick()
    const ta = document.querySelector('textarea')
    if (ta) { ta.focus(); ta.setSelectionRange(inputText.value.length, inputText.value.length) }
  } catch { /* 静默 */ }
  finally { optimizing.value = false }
}

async function handleSend() {
  const text = inputText.value.trim()
  const hasImages = previewImages.value.length > 0
  if (!text && !hasImages) return
  if (loading.value) return

  if (followUpMode.value) {
    comboCount.value += 1
  } else {
    comboCount.value = 0
  }

  inputText.value = ''
  const images = [...previewImages.value]
  previewImages.value = []
  images.forEach(img => URL.revokeObjectURL(img.url))

  const userMsg = {
    id: Date.now(),
    role: 'user',
    content: text || '(图片)',
    _combo: followUpMode.value ? comboCount.value : 0,
  }
  messages.value.push(userMsg)
  loading.value = true
  await nextTick()
  scrollToBottom()

  try {
    const res = hasImages
      ? await uploadImage(text, images[0].file, userStore.deepMode)
      : await sendMessage(text, userStore.deepMode, followUpMode.value)
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: res.content,
      model_used: res.model_used,
    })
  } catch (err) {
    messages.value.push({ id: Date.now() + 1, role: 'assistant', content: `❌ ${err.message}` })
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight
}

function renderMarkdown(text) {
  if (!text) return ''
  let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  html = html.replace(/\$\$([\s\S]*?)\$\$/g, (_, f) => {
    try { return katex.renderToString(f.trim(), { displayMode: true, throwOnError: false }) }
    catch { return `<div class="formula-error">$${f}$$</div>` }
  })
  html = html.replace(/\$([^$\n]+?)\$/g, (_, f) => {
    try { return katex.renderToString(f.trim(), { displayMode: false, throwOnError: false }) }
    catch { return `<span class="formula-error">$${f}$</span>` }
  })
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\n/g, '<br />')
  return html
}
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 112px);
}

/* ── 头部 ── */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.chat-header h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--ink-900);
}

.header-toggles {
  display: flex;
  gap: 8px;
}

.toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  user-select: none;
  padding: 5px 12px;
  border-radius: 8px;
  border: 1.5px solid var(--neutral-300);
  transition: all 0.2s ease;
  background: var(--surface);
}
.toggle:hover {
  border-color: var(--neutral-400);
}
.toggle:has(input:checked) {
  border-color: var(--ink-700);
  background: var(--ink-50);
}
.toggle input {
  cursor: pointer;
  accent-color: var(--ink-700);
}
.toggle-label {
  font-size: 13px;
  color: var(--neutral-600);
  font-weight: 500;
  transition: color 0.2s;
}
.toggle:has(input:checked) .toggle-label {
  color: var(--ink-900);
  font-weight: 600;
}

/* ── 对话区 ── */
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  margin-bottom: 14px;
  box-shadow: var(--shadow-sm);
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 22px;
  animation: fadeIn 0.35s ease-out;
  position: relative;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.msg-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
  background: var(--bg-elevated);
}

.user-msg {
  flex-direction: row-reverse;
}

.user-msg .msg-avatar {
  background: var(--ink-50);
}

.user-msg .msg-content {
  background: var(--ink-900);
  color: #fff;
  border-radius: 18px 6px 18px 18px;
}

.ai-msg .msg-avatar {
  background: var(--amber-50);
}

.ai-msg .msg-content {
  background: #FCFBF8;
  border: 1px solid var(--neutral-200);
  border-left: 4px solid var(--amber-500);
  border-radius: 6px 18px 18px 18px;
}

.msg-content {
  max-width: 78%;
  padding: 12px 20px;
  line-height: 1.75;
  font-size: 14px;
  box-shadow: var(--shadow-sm);
}

.msg-image {
  max-width: 100%;
  border-radius: 8px;
  margin-bottom: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.msg-text :deep(.formula) {
  overflow-x: auto;
  padding: 4px 0;
}
.msg-text :deep(pre) {
  background: #F1F0EC;
  padding: 12px 14px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.6;
  margin: 8px 0;
}
.msg-text :deep(code) {
  font-family: var(--font-mono);
  font-size: 13px;
  background: #F1F0EC;
  padding: 1px 5px;
  border-radius: 3px;
}
.msg-meta {
  font-size: 11px;
  color: var(--neutral-400);
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid rgba(255,255,255,0.1);
}

.user-msg .msg-meta {
  color: rgba(255, 255, 255, 0.5);
  border-top-color: rgba(255, 255, 255, 0.1);
}

/* ── Combo 连击标记 ── */
.combo-tag {
  position: absolute;
  top: -12px;
  right: -8px;
  background: linear-gradient(135deg, var(--amber-500), var(--rose-600));
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  padding: 2px 12px;
  border-radius: 20px;
  box-shadow: 0 2px 10px rgba(217, 119, 6, 0.35);
  animation: comboPop 1.5s ease-out forwards;
  pointer-events: none;
}
@keyframes comboPop {
  0% { transform: scale(0.5) translateY(10px); opacity: 0; }
  20% { transform: scale(1.2) translateY(-4px); opacity: 1; }
  40% { transform: scale(1) translateY(0); opacity: 1; }
  70% { opacity: 1; }
  100% { transform: translateY(-20px); opacity: 0; }
}

/* ── 打字动画 ── */
.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 6px 0;
}
.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--amber-500);
  animation: bounce 1.4s infinite ease-in-out;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.16s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.32s; }
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-10px); }
}

/* ── 输入区 ── */
.input-area {
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 14px 16px;
  background: var(--surface);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.2s;
}
.input-area:focus-within {
  box-shadow: 0 0 0 3px rgba(43, 74, 122, 0.06), var(--shadow-md);
}

.image-previews {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.preview-item {
  position: relative;
  width: 90px;
  height: 90px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}
.preview-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.remove-img {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: none;
  background: var(--neutral-600);
  color: #fff;
  cursor: pointer;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.85;
  transition: opacity 0.15s;
}
.remove-img:hover {
  opacity: 1;
}

.input-row {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.tool-btn {
  background: none;
  border: 1.5px solid var(--neutral-300);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  transition: all 0.15s ease;
  flex-shrink: 0;
  color: var(--neutral-500);
}
.tool-btn:hover {
  border-color: var(--ink-700);
  background: var(--ink-50);
  color: var(--ink-700);
}
.tool-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.optimize-btn {
  font-size: 16px;
}
.optimizing-spinner {
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  padding: 8px 4px;
  font-size: 14px;
  font-family: var(--font-body);
  line-height: 1.6;
  color: var(--text-primary);
  background: transparent;
}
textarea::placeholder {
  color: var(--neutral-400);
}

.send-btn {
  padding: 8px 24px;
  background: var(--ink-900);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.send-btn:hover:not(:disabled) {
  background: var(--ink-800);
  box-shadow: var(--shadow-sm);
}
.send-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
</style>
