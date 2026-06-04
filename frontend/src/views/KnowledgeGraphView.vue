<template>
  <div class="kg-container">
    <!-- 顶栏 -->
    <div class="kg-topbar">
      <div class="kg-title">
        <h2>🧠 知识图谱</h2>
        <span class="kg-subtitle">高中物理 · 知识点关联网络</span>
      </div>
      <div class="kg-legend">
        <span v-for="s in subjects" :key="s.key" class="legend-item">
          <span class="legend-dot" :style="{ background: s.color }"></span>
          {{ s.label }}
        </span>
      </div>
      <div class="kg-controls">
        <button class="ctrl-btn" @click="handleReset" title="重置视角">⟲</button>
        <button class="ctrl-btn" @click="handleLayout" title="重新布局">⟳</button>
      </div>
    </div>

    <!-- Canvas 画布 -->
    <div class="kg-canvas-wrap" ref="canvasWrap" @contextmenu.prevent>
      <canvas ref="canvasRef" @mousedown="onPointerDown" @mousemove="onPointerMove" @mouseup="onPointerUp"
        @wheel.prevent="onWheel" @click="onCanvasClick" @dblclick="onCanvasDblClick" @contextmenu="onCanvasContext"
        @touchstart.prevent="onTouchStart" @touchmove.prevent="onTouchMove" @touchend.prevent="onTouchEnd">
      </canvas>

      <!-- 加载中 -->
      <div v-if="loading" class="kg-loading">
        <div class="kg-spinner"></div>
        <span>加载知识图谱...</span>
      </div>

      <!-- 节点信息卡片 -->
      <transition name="card-pop">
        <div v-if="selectedNode" class="node-card" :style="cardStyle">
          <div class="card-head" :style="{ borderLeftColor: getSubjectColor(selectedNode.subject) }">
            <h3>{{ selectedNode.label }}</h3>
            <span class="card-badge" :style="{ background: getSubjectColor(selectedNode.subject) }">
              {{ subjectLabel(selectedNode.subject) }}
            </span>
          </div>
          <p class="card-desc">{{ selectedNode.description }}</p>
          <div class="card-meta">
            <span class="card-type">{{ categoryLabel(selectedNode.category) }}</span>
            <span v-if="selectedNode.importance" class="card-imp">
              {{ '★'.repeat(selectedNode.importance) }}{{ '☆'.repeat(5 - selectedNode.importance) }}
            </span>
          </div>
          <div v-if="selectedNode.mastery !== undefined" class="card-mastery">
            <span class="mastery-label">掌握度</span>
            <div class="mastery-bar">
              <div class="mastery-fill" :style="{ width: (selectedNode.mastery || 0) * 100 + '%', background: masteryColor(selectedNode.mastery) }"></div>
            </div>
            <span class="mastery-val">{{ Math.round((selectedNode.mastery || 0) * 100) }}%</span>
          </div>
          <div class="card-actions">
            <button v-for="mt in markerTypes" :key="mt.key"
              :class="['marker-btn', { active: (selectedNode.markers || []).includes(mt.key) }]"
              :style="{ borderColor: (selectedNode.markers || []).includes(mt.key) ? mt.color : 'transparent' }"
              @click="toggleNodeMarker(selectedNode, mt.key)"
              :title="mt.label">
              {{ mt.icon }}
            </button>
          </div>
          <button class="card-close" @click="selectedNode = null">✕</button>
        </div>
      </transition>

      <!-- 图例（移动端） -->
      <div v-if="isMobile && !selectedNode" class="mobile-legend">
        <span v-for="s in subjects" :key="s.key" class="legend-dot" :style="{ background: s.color }"></span>
      </div>

      <!-- 右下角图例 -->
      <div class="canvas-legend">
        <div class="cl-row"><span class="cl-dot" style="background:#EF4444"></span>薄弱</div>
        <div class="cl-row"><span class="cl-dot" style="background:#FBBF24"></span>重点</div>
        <div class="cl-row"><span class="cl-dot" style="background:#22C55E"></span>收藏</div>
      </div>

      <!-- 右键标记菜单 -->
      <transition name="menu-pop">
        <div v-if="markerMenu" class="ctx-menu" :style="{ left: markerMenu.x + 'px', top: markerMenu.y + 'px' }">
          <div class="ctx-header">{{ markerMenu.node.label }}</div>
          <button v-for="mt in markerTypes" :key="mt.key"
            :class="['ctx-item', { active: (markerMenu.node.markers || []).includes(mt.key) }]"
            @click="toggleNodeMarker(markerMenu.node, mt.key)">
            <span>{{ (markerMenu.node.markers || []).includes(mt.key) ? '✓' : mt.icon }}</span>
            {{ mt.label }}
          </button>
          <div class="ctx-divider"></div>
          <button class="ctx-item ctx-cancel" @click="closeMarkerMenu">取消</button>
        </div>
      </transition>

      <!-- Toast -->
      <transition name="toast-pop">
        <div v-if="markerToast" class="kg-toast">{{ markerToast }}</div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { getKnowledgeGraph, addMarker, removeMarker } from '../api/knowledge'

// ── 配色系统 ──
const SUBJECT_COLORS = {
  mechanics: '#38BDF8',
  electromagnetism: '#FBBF24',
  thermodynamics: '#FB7185',
  optics: '#34D399',
  modern: '#A78BFA',
}
const SUBJECT_GLOW = {
  mechanics: 'rgba(56,189,248,0.35)',
  electromagnetism: 'rgba(251,191,36,0.35)',
  thermodynamics: 'rgba(251,113,133,0.35)',
  optics: 'rgba(52,211,153,0.35)',
  modern: 'rgba(167,139,250,0.35)',
}
const subjects = [
  { key: 'mechanics', label: '力学', color: SUBJECT_COLORS.mechanics },
  { key: 'electromagnetism', label: '电学', color: SUBJECT_COLORS.electromagnetism },
  { key: 'thermodynamics', label: '热学', color: SUBJECT_COLORS.thermodynamics },
  { key: 'optics', label: '光学', color: SUBJECT_COLORS.optics },
  { key: 'modern', label: '近代物理', color: SUBJECT_COLORS.modern },
]
const markerTypes = [
  { key: 'bookmark', label: '收藏', icon: '🔖', color: '#22C55E' },
  { key: 'weak', label: '薄弱', icon: '🔴', color: '#EF4444' },
  { key: 'important', label: '重点', icon: '⭐', color: '#FBBF24' },
]

function getSubjectColor(s) { return SUBJECT_COLORS[s] || '#94A3B8' }
function subjectLabel(s) { return subjects.find(x => x.key === s)?.label || s || '' }
function categoryLabel(c) { return { chapter: '📖 章', section: '📂 节', topic: '📍 知识点' }[c] || '' }
function masteryColor(v) {
  if (v === null || v === undefined) return '#94A3B8'
  return v < 0.3 ? '#EF4444' : v < 0.6 ? '#F59E0B' : '#22C55E'
}

// ── 状态 ──
const canvasRef = ref(null)
const canvasWrap = ref(null)
const loading = ref(true)
const selectedNode = ref(null)
const cardStyle = ref({})
const isMobile = ref(window.innerWidth < 768)
const markerMenu = ref(null)   // { node, x, y } | null
const markerToast = ref('')

let ctx = null
let W = 0, H = 0
let nodes = []
let edges = []
let nodeMap = {}
let simRunning = false
let animFrame = null
let pointer = { x: 0, y: 0, down: false, moved: false, dragNode: null }
let view = { x: 0, y: 0, scale: 1 }
let stars = []
let edgeParticles = []
let hoveredNode = null
let settled = false

// ── 加载 ──
onMounted(async () => {
  window.addEventListener('resize', onResize)
  await loadGraph()
  nextTick(() => { initCanvas(); startLoop() })
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (animFrame) cancelAnimationFrame(animFrame)
})

async function loadGraph() {
  try {
    const res = await getKnowledgeGraph()
    const raw = res.groups ? res : res
    const data = raw.nodes || raw
    // 支持两种格式：{nodes, edges} 或直接数组
    if (Array.isArray(data)) {
      nodes = data
      edges = raw.edges || []
    } else {
      nodes = data.nodes || []
      edges = data.edges || []
    }
    // 从 parent 生成包含边
    const existingSet = new Set(edges.map(e => `${e.source}-${e.target}`))
    for (const n of nodes) {
      if (n.parent && !existingSet.has(`${n.parent}-${n.id}`)) {
        edges.push({ source: n.parent, target: n.id, type: 'contains', label: '' })
        existingSet.add(`${n.parent}-${n.id}`)
      }
    }
    nodeMap = {}
    nodes.forEach(n => { nodeMap[n.id] = n })
    initGraphLayout()
  } catch {
    // fallback
  } finally {
    loading.value = false
  }
}

// ── 力导向布局 ──
function initGraphLayout() {
  const cx = 0, cy = 0
  const radius = Math.min(300, nodes.length * 4)
  // 按学科分组分层放置
  const subjects = [...new Set(nodes.map(n => n.subject))]
  const angleStep = (Math.PI * 2) / subjects.length
  subjects.forEach((subj, si) => {
    const subjNodes = nodes.filter(n => n.subject === subj)
    const sa = si * angleStep
    const sc = { x: cx + Math.cos(sa) * radius * 0.6, y: cy + Math.sin(sa) * radius * 0.6 }
    subjNodes.forEach((n, i) => {
      const t = i / subjNodes.length * Math.PI * 2
      const r = radius * (n.category === 'topic' ? 0.35 : n.category === 'section' ? 0.2 : 0.1)
      n.x = sc.x + Math.cos(t) * r + (Math.random() - 0.5) * 20
      n.y = sc.y + Math.sin(t) * r + (Math.random() - 0.5) * 20
      n.vx = 0; n.vy = 0
      n.radius = n.category === 'chapter' ? 26 : n.category === 'section' ? 20 : 14
      n.mastery = n.mastery ?? null
    })
  })
  generateStars()
  startSimulation()
}

function generateStars() {
  stars = Array.from({ length: 80 }, () => ({
    x: Math.random() * 2000 - 1000,
    y: Math.random() * 2000 - 1000,
    r: Math.random() * 1.5 + 0.3,
    a: Math.random() * 0.6 + 0.2,
    s: Math.random() * 0.2 + 0.05,
  }))
}

function startSimulation() {
  if (simRunning) return
  simRunning = true
  settled = false
}

function stopSimulation() {
  simRunning = false
  settled = true
}

function simulate() {
  if (!simRunning) return
  const repulsion = 6000
  const attraction = 0.005
  const damping = 0.85
  const centerForce = 0.002
  const edgeRest = 120

  // Reset forces
  for (const n of nodes) { n.fx = 0; n.fy = 0 }

  // Repulsion (Barnes-Hut 近似：不考虑远处细节)
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const a = nodes[i], b = nodes[j]
      let dx = b.x - a.x, dy = b.y - a.y
      let dist = Math.sqrt(dx * dx + dy * dy) || 1
      const force = repulsion / (dist * dist)
      const fx = dx / dist * force, fy = dy / dist * force
      a.fx -= fx; a.fy -= fy
      b.fx += fx; b.fy += fy
    }
  }

  // Attraction along edges
  const edgeSet = new Map()
  for (const e of edges) {
    const a = nodeMap[e.source], b = nodeMap[e.target]
    if (!a || !a.x == null || !b || b.x == null) continue
    const key = [e.source, e.target].sort().join('-')
    if (edgeSet.has(key)) continue
    edgeSet.set(key, true)
    let dx = b.x - a.x, dy = b.y - a.y
    let dist = Math.sqrt(dx * dx + dy * dy) || 1
    const rest = Math.min(edgeRest * (a.radius + b.radius) / 20, 250)
    const force = (dist - rest) * attraction
    const fx = dx / dist * force, fy = dy / dist * force
    a.fx += fx; a.fy += fy
    b.fx -= fx; b.fy -= fy
  }

  // Center force
  for (const n of nodes) {
    n.fx -= n.x * centerForce
    n.fy -= n.y * centerForce
  }

  // Apply
  let maxVel = 0
  for (const n of nodes) {
    if (n._pinned) continue
    n.vx = (n.vx + n.fx) * damping
    n.vy = (n.vy + n.fy) * damping
    n.x += n.vx
    n.y += n.vy
    const v = Math.sqrt(n.vx * n.vx + n.vy * n.vy)
    if (v > maxVel) maxVel = v
  }

  if (maxVel < 0.05) {
    stopSimulation()
  }
}

// ── Canvas 渲染 ──
function initCanvas() {
  ctx = canvasRef.value.getContext('2d')
  onResize()
}

function onResize() {
  if (!canvasWrap.value) return
  const rect = canvasWrap.value.getBoundingClientRect()
  W = rect.width; H = rect.height
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  canvasRef.value.width = W * dpr
  canvasRef.value.height = H * dpr
  canvasRef.value.style.width = W + 'px'
  canvasRef.value.style.height = H + 'px'
  ctx = canvasRef.value.getContext('2d')
  ctx.scale(dpr, dpr)
}

function worldToScreen(wx, wy) {
  return { x: wx * view.scale + view.x + W / 2, y: wy * view.scale + view.y + H / 2 }
}
function screenToWorld(sx, sy) {
  return { x: (sx - view.x - W / 2) / view.scale, y: (sy - view.y - H / 2) / view.scale }
}

function drawScene() {
  if (!ctx) return
  ctx.clearRect(0, 0, W, H)

  // Background
  const grad = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, Math.max(W, H) * 0.7)
  grad.addColorStop(0, '#11152E')
  grad.addColorStop(1, '#070913')
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, W, H)

  ctx.save()
  ctx.translate(W / 2 + view.x, H / 2 + view.y)
  ctx.scale(view.scale, view.scale)

  // Stars
  for (const star of stars) {
    ctx.globalAlpha = star.a + Math.sin(Date.now() * 0.001 * star.s) * 0.15
    ctx.fillStyle = '#fff'
    ctx.beginPath()
    ctx.arc(star.x, star.y, star.r, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalAlpha = 1

  // Edges
  for (const e of edges) {
    const a = nodeMap[e.source], b = nodeMap[e.target]
    if (!a || a.x == null || !b || b.x == null) continue
    const color = e.type === 'contains'
      ? 'rgba(255,255,255,0.06)'
      : e.type === 'prerequisite' ? 'rgba(56,189,248,0.15)' : 'rgba(255,255,255,0.1)'
    ctx.strokeStyle = color
    ctx.lineWidth = e.type === 'contains' ? 0.8 : 1.2
    ctx.beginPath()
    ctx.moveTo(a.x, a.y)
    ctx.lineTo(b.x, b.y)
    ctx.stroke()

    // Arrow for prerequisite
    if (e.type === 'prerequisite') {
      const dx = b.x - a.x, dy = b.y - a.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      const mx = a.x + dx * 0.85, my = a.y + dy * 0.85
      const angle = Math.atan2(dy, dx)
      ctx.fillStyle = 'rgba(56,189,248,0.25)'
      ctx.beginPath()
      ctx.moveTo(mx + Math.cos(angle - 0.4) * 6, my + Math.sin(angle - 0.4) * 6)
      ctx.lineTo(mx + Math.cos(angle + 0.4) * 6, my + Math.sin(angle + 0.4) * 6)
      ctx.lineTo(mx + Math.cos(angle) * 10, my + Math.sin(angle) * 10)
      ctx.fill()
    }
  }

  // Edge particles
  updateParticles()
  for (const p of edgeParticles) {
    ctx.fillStyle = p.color
    ctx.shadowColor = p.color
    ctx.shadowBlur = 8
    ctx.beginPath()
    ctx.arc(p.x, p.y, 2, 0, Math.PI * 2)
    ctx.fill()
    ctx.shadowBlur = 0
  }

  // Nodes
  // Sort: draw larger nodes first so smaller ones sit on top
  const sorted = [...nodes].sort((a, b) => (a.radius || 10) - (b.radius || 10))
  for (const n of sorted) {
    const color = getSubjectColor(n.subject)
    const glow = SUBJECT_GLOW[n.subject] || 'rgba(148,163,184,0.2)'
    const r = n.radius || 14
    const isHover = hoveredNode === n.id
    const isSelected = selectedNode.value?.id === n.id
    const isWeak = n.mastery !== null && n.mastery !== undefined && n.mastery < 0.4

    // Glow
    ctx.shadowColor = isHover || isSelected ? color : glow
    ctx.shadowBlur = isHover ? 25 : isSelected ? 20 : 12

    // Node circle
    const alpha = isWeak ? 1 : isHover || isSelected ? 1 : 0.85
    ctx.globalAlpha = alpha
    const grad2 = ctx.createRadialGradient(n.x - r * 0.3, n.y - r * 0.3, 0, n.x, n.y, r)
    grad2.addColorStop(0, '#fff')
    grad2.addColorStop(0.15, color)
    grad2.addColorStop(0.85, color)
    grad2.addColorStop(1, adjustColor(color, -40))
    ctx.fillStyle = grad2
    ctx.beginPath()
    ctx.arc(n.x, n.y, r, 0, Math.PI * 2)
    ctx.fill()

    // Weak pulse ring
    if (isWeak) {
      const pulse = Math.sin(Date.now() * 0.004) * 0.3 + 0.7
      ctx.strokeStyle = `rgba(239,68,68,${pulse * 0.6})`
      ctx.lineWidth = 2
      ctx.shadowBlur = 15
      ctx.shadowColor = '#EF4444'
      ctx.beginPath()
      ctx.arc(n.x, n.y, r + 4 + (1 - pulse) * 3, 0, Math.PI * 2)
      ctx.stroke()
    }

    ctx.globalAlpha = 1
    ctx.shadowBlur = 0

    // Label
    if (view.scale > 0.3) {
      const fontSize = n.category === 'chapter' ? 11 : n.category === 'section' ? 10 : 9
      ctx.font = `${fontSize}px "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.fillStyle = isHover || isSelected ? '#fff' : 'rgba(255,255,255,0.75)'
      const labelY = n.y + r + 4
      // Truncate
      let label = n.label || n.id
      if (view.scale < 0.6 && label.length > 4) label = label.slice(0, 4) + '..'
      ctx.fillText(label, n.x, labelY)
    }

    // 学科缩写（章节点显示）
    if (n.category === 'chapter') {
      ctx.font = 'bold 12px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = '#fff'
      const abbr = { mechanics: '力', electromagnetism: '电', thermodynamics: '热', optics: '光', modern: '近' }[n.subject] || ''
      ctx.fillText(abbr, n.x, n.y + 1)
    }

    // 标记小图标
    if (n.markers && n.markers.length > 0 && view.scale > 0.4) {
      const iconY = n.y + r + (view.scale > 0.6 ? 18 : 14)
      let iconX = n.x - (n.markers.length - 1) * 7
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      for (const m of n.markers) {
        const icon = { bookmark: '🔖', weak: '⚠️', important: '⭐' }[m] || ''
        ctx.fillText(icon, iconX, iconY)
        iconX += 14
      }
    }
  }

  ctx.restore()
}

let particleTimer = 0
function updateParticles() {
  particleTimer += 1
  if (edgeParticles.length < 30 && particleTimer % 8 === 0) {
    const validEdges = edges.filter(e => {
      const a = nodeMap[e.source], b = nodeMap[e.target]
      return a && a.x != null && b && b.x != null
    })
    if (validEdges.length > 0) {
      const e = validEdges[Math.floor(Math.random() * validEdges.length)]
      const a = nodeMap[e.source], b = nodeMap[e.target]
      edgeParticles.push({
        x: a.x, y: a.y,
        targetX: b.x, targetY: b.y,
        t: 0,
        speed: 0.005 + Math.random() * 0.01,
        color: getSubjectColor(a.subject || b.subject),
      })
    }
  }
  edgeParticles = edgeParticles.filter(p => {
    p.t += p.speed
    if (p.t >= 1) return false
    p.x += (p.targetX - p.x) * p.speed * 3
    p.y += (p.targetY - p.y) * p.speed * 3
    return true
  })
}

function adjustColor(hex, amount) {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = Math.min(255, Math.max(0, (num >> 16) + amount))
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0xFF) + amount))
  const b = Math.min(255, Math.max(0, (num & 0xFF) + amount))
  return `rgb(${r},${g},${b})`
}

// ── 动画循环 ──
function startLoop() {
  function tick() {
    if (simRunning) simulate()
    drawScene()
    animFrame = requestAnimationFrame(tick)
  }
  tick()
}

// ── 交互 ──
function hitTest(sx, sy) {
  const w = screenToWorld(sx, sy)
  // 反向遍历（上层节点优先）
  for (let i = nodes.length - 1; i >= 0; i--) {
    const n = nodes[i]
    if (n.x == null) continue
    const dx = w.x - n.x, dy = w.y - n.y
    const r = (n.radius || 14) + 4
    if (dx * dx + dy * dy < r * r) return n
  }
  return null
}

function onPointerDown(e) {
  pointer.down = true
  pointer.moved = false
  pointer.x = e.clientX
  pointer.y = e.clientY
  const n = hitTest(e.offsetX, e.offsetY)
  pointer.dragNode = n
  if (n) { n._pinned = true }
}

function onPointerMove(e) {
  const dx = e.clientX - pointer.x, dy = e.clientY - pointer.y
  if (pointer.down && (Math.abs(dx) > 3 || Math.abs(dy) > 3)) {
    pointer.moved = true
  }
  if (pointer.dragNode && pointer.down) {
    const w = screenToWorld(e.offsetX, e.offsetY)
    pointer.dragNode.x = w.x
    pointer.dragNode.y = w.y
    startSimulation()
  } else if (pointer.down) {
    view.x += dx
    view.y += dy
  }
  pointer.x = e.clientX
  pointer.y = e.clientY

  // Hover
  if (!pointer.down) {
    const n = hitTest(e.offsetX, e.offsetY)
    hoveredNode = n?.id || null
    canvasRef.value.style.cursor = n ? 'pointer' : 'grab'
  }
}

function onPointerUp(e) {
  if (pointer.dragNode) {
    pointer.dragNode._pinned = false
    pointer.dragNode = null
  }
  pointer.down = false
}

function onWheel(e) {
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  const mx = e.offsetX, my = e.offsetY
  view.scale *= delta
  view.scale = Math.max(0.15, Math.min(3, view.scale))
  view.x = mx - (mx - view.x) * delta
  view.y = my - (my - view.y) * delta
}

function onCanvasClick(e) {
  if (pointer.moved) return
  const n = hitTest(e.offsetX, e.offsetY)
  if (n) {
    selectedNode.value = n
    const rect = canvasRef.value.getBoundingClientRect()
    const pos = worldToScreen(n.x, n.y)
    const cardW = 260
    let cardX = pos.x + 30
    let cardY = pos.y - 80
    if (cardX + cardW > W - 20) cardX = pos.x - cardW - 20
    if (cardY < 10) cardY = 10
    if (cardY > H - 200) cardY = H - 220
    cardStyle.value = { left: cardX + 'px', top: cardY + 'px' }
  } else {
    selectedNode.value = null
  }
}

function onCanvasDblClick(e) {
  const n = hitTest(e.offsetX, e.offsetY)
  if (!n) return
  const w = screenToWorld(e.offsetX, e.offsetY)
  view.scale = Math.min(2, view.scale * 1.3)
  view.x = e.offsetX - (w.x * view.scale)
  view.y = e.offsetY - (w.y * view.scale)
  onCanvasClick(e)
}

function onCanvasContext(e) {
  e.preventDefault()
  const n = hitTest(e.offsetX, e.offsetY)
  if (n) {
    markerMenu.value = { node: n, x: e.clientX, y: e.clientY }
  } else {
    markerMenu.value = null
  }
}

function closeMarkerMenu() { markerMenu.value = null }

async function toggleNodeMarker(node, type) {
  const markers = node.markers || []
  const has = markers.includes(type)
  try {
    if (has) {
      await removeMarker(node.id, type)
      node.markers = markers.filter(m => m !== type)
      showToast(getMarkerLabel(type) + ' 已取消')
    } else {
      await addMarker(node.id, type)
      node.markers = [...markers, type]
      showToast(getMarkerLabel(type) + ' 已标记')
    }
  } catch { showToast('操作失败') }
  markerMenu.value = null
}

function getMarkerLabel(t) {
  return { bookmark: '📑 收藏', weak: '🔴 薄弱', important: '⭐ 重点' }[t] || t
}

let toastTimer = null
function showToast(msg) {
  markerToast.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { markerToast.value = '' }, 2000)
}

// ── 触屏支持 ──
let touchState = { dist: 0 }
function onTouchStart(e) {
  if (e.touches.length === 1) {
    const t = e.touches[0]
    pointer.down = true; pointer.moved = false
    pointer.x = t.clientX; pointer.y = t.clientY
    const rect = canvasRef.value.getBoundingClientRect()
    const n = hitTest(t.clientX - rect.left, t.clientY - rect.top)
    pointer.dragNode = n
    if (n) n._pinned = true
  } else if (e.touches.length === 2) {
    touchState.dist = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY)
  }
}
function onTouchMove(e) {
  if (e.touches.length === 2) {
    const dist = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY)
    const scale = dist / touchState.dist
    view.scale *= scale
    view.scale = Math.max(0.15, Math.min(3, view.scale))
    touchState.dist = dist
    return
  }
  if (e.touches.length !== 1) return
  const t = e.touches[0]
  const dx = t.clientX - pointer.x, dy = t.clientY - pointer.y
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) pointer.moved = true
  if (pointer.dragNode && pointer.down) {
    const rect = canvasRef.value.getBoundingClientRect()
    const w = screenToWorld(t.clientX - rect.left, t.clientY - rect.top)
    pointer.dragNode.x = w.x; pointer.dragNode.y = w.y
    startSimulation()
  } else if (pointer.down) {
    view.x += dx; view.y += dy
  }
  pointer.x = t.clientX; pointer.y = t.clientY
}
function onTouchEnd(e) {
  if (pointer.dragNode) { pointer.dragNode._pinned = false; pointer.dragNode = null }
  pointer.down = false
  if (!pointer.moved && e.changedTouches.length === 1) {
    const rect = canvasRef.value.getBoundingClientRect()
    const t = e.changedTouches[0]
    onCanvasClick({ offsetX: t.clientX - rect.left, offsetY: t.clientY - rect.top, clientX: t.clientX, clientY: t.clientY })
  }
}

// ── 控制按钮 ──
function handleReset() {
  view.x = 0; view.y = 0; view.scale = 1
  initGraphLayout()
}
function handleLayout() {
  initGraphLayout()
}

// ── 兼容 ──
window.addEventListener('resize', () => {
  isMobile.value = window.innerWidth < 768
})
</script>

<style scoped>
.kg-container {
  height: calc(100vh - 112px);
  display: flex;
  flex-direction: column;
}

/* ── 顶栏 ── */
.kg-topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.kg-title {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.kg-title h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--ink-900);
}
.kg-subtitle {
  font-size: 13px;
  color: var(--neutral-500);
}
.kg-legend {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--neutral-500);
}
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.kg-controls {
  margin-left: auto;
  display: flex;
  gap: 6px;
}
.ctrl-btn {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  border: 1.5px solid var(--neutral-300);
  background: var(--surface);
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--neutral-600);
  transition: all 0.15s;
}
.ctrl-btn:hover {
  border-color: var(--ink-700);
  color: var(--ink-700);
  background: var(--ink-50);
}

/* ── Canvas ── */
.kg-canvas-wrap {
  flex: 1;
  position: relative;
  border-radius: var(--radius-xl);
  overflow: hidden;
  background: #070913;
  border: 1px solid var(--border);
}
.kg-canvas-wrap canvas {
  display: block;
  width: 100%;
  height: 100%;
}

/* ── 加载中 ── */
.kg-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: rgba(255,255,255,0.5);
  font-size: 14px;
  z-index: 2;
}
.kg-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(255,255,255,0.1);
  border-top-color: #38BDF8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 节点信息卡片 ── */
.node-card {
  position: absolute;
  width: 260px;
  background: rgba(15, 20, 45, 0.95);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 14px;
  padding: 20px;
  z-index: 10;
  color: #E8E6E3;
  box-shadow: 0 8px 40px rgba(0,0,0,0.6);
}
.card-head {
  border-left: 3px solid;
  padding-left: 12px;
  margin-bottom: 10px;
}
.card-head h3 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}
.card-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
}
.card-desc {
  font-size: 13px;
  line-height: 1.6;
  color: rgba(255,255,255,0.7);
  margin: 0 0 12px;
}
.card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: rgba(255,255,255,0.4);
}
.card-type {
  background: rgba(255,255,255,0.06);
  padding: 2px 8px;
  border-radius: 4px;
}
.card-imp {
  font-size: 13px;
  letter-spacing: 1px;
}
.card-mastery {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255,255,255,0.08);
  display: flex;
  align-items: center;
  gap: 8px;
}
.mastery-label {
  font-size: 12px;
  color: rgba(255,255,255,0.5);
  white-space: nowrap;
}
.mastery-bar {
  flex: 1;
  height: 5px;
  background: rgba(255,255,255,0.08);
  border-radius: 3px;
  overflow: hidden;
}
.mastery-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.4s ease;
}
.mastery-val {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255,255,255,0.6);
  min-width: 32px;
  text-align: right;
}
.card-close {
  position: absolute;
  top: 10px;
  right: 12px;
  background: none;
  border: none;
  color: rgba(255,255,255,0.3);
  cursor: pointer;
  font-size: 14px;
  padding: 4px;
  border-radius: 4px;
}
.card-close:hover {
  color: #fff;
  background: rgba(255,255,255,0.1);
}

.card-pop-enter-active { transition: all 0.2s ease-out; }
.card-pop-leave-active { transition: all 0.15s ease-in; }
.card-pop-enter-from { opacity: 0; transform: translateY(8px) scale(0.95); }
.card-pop-leave-to { opacity: 0; transform: translateY(4px) scale(0.97); }

/* ── 卡片标记按钮 ── */
.card-actions {
  display: flex;
  gap: 6px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255,255,255,0.08);
}
.marker-btn {
  flex: 1;
  padding: 6px 0;
  border: 1.5px solid transparent;
  border-radius: var(--radius-sm);
  background: rgba(255,255,255,0.05);
  cursor: pointer;
  font-size: 16px;
  transition: all 0.15s;
}
.marker-btn:hover { background: rgba(255,255,255,0.1); }
.marker-btn.active {
  background: rgba(255,255,255,0.1);
  box-shadow: 0 0 0 1px currentColor;
}

/* ── 右键菜单 ── */
.ctx-menu {
  position: fixed;
  z-index: 50;
  min-width: 160px;
  background: rgba(20,25,55,0.97);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 6px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.5);
}
.ctx-header {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255,255,255,0.5);
  padding: 8px 12px 6px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  margin-bottom: 4px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ctx-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  background: none;
  border: none;
  color: rgba(255,255,255,0.8);
  font-size: 13px;
  cursor: pointer;
  border-radius: 6px;
  text-align: left;
  transition: background 0.1s;
}
.ctx-item:hover { background: rgba(255,255,255,0.08); }
.ctx-item.active { color: #38BDF8; }
.ctx-divider { height: 1px; background: rgba(255,255,255,0.06); margin: 4px 0; }
.ctx-cancel { color: rgba(255,255,255,0.4); }

.menu-pop-enter-active { transition: all 0.15s ease-out; }
.menu-pop-leave-active { transition: all 0.1s ease-in; }
.menu-pop-enter-from, .menu-pop-leave-to { opacity: 0; transform: scale(0.95); }

/* ── Toast ── */
.kg-toast {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(15,20,45,0.92);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.1);
  color: #E8E6E3;
  padding: 10px 24px;
  border-radius: 24px;
  font-size: 14px;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0,0,0,0.4);
  pointer-events: none;
}
.toast-pop-enter-active { transition: all 0.2s ease-out; }
.toast-pop-leave-active { transition: all 0.2s ease-in; }
.toast-pop-enter-from { opacity: 0; transform: translateX(-50%) translateY(-10px); }
.toast-pop-leave-to { opacity: 0; transform: translateX(-50%) translateY(-6px); }

/* ── 右下角图例 ── */
.canvas-legend {
  position: absolute;
  bottom: 16px;
  right: 16px;
  background: rgba(0,0,0,0.5);
  padding: 10px 14px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11px;
  color: rgba(255,255,255,0.5);
  pointer-events: none;
}
.cl-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.cl-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

/* ── 移动端 ── */
.mobile-legend {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  background: rgba(0,0,0,0.5);
  padding: 8px 14px;
  border-radius: 20px;
}
.mobile-legend .legend-dot {
  width: 12px;
  height: 12px;
}

@media (max-width: 767px) {
  .kg-topbar {
    gap: 8px;
  }
  .kg-subtitle { display: none; }
  .kg-legend { display: none; }
}
</style>
