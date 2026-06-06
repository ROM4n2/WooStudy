# 📘 WooStudy — 高中物理 AI 助学

> 基于 Vue3 + FastAPI + SQLite 的高中物理 AI 助学 Web 应用。  
> 含多模态答疑、AI 错题本、智能刷题、虚拟实验室、知识图谱、学情分析等完整模块。  
> 双模型架构：Mimo（L1 多模态识图/基础问答）+ DeepSeek V4 Pro（L2 深度推理）。

---

## 功能全景

| 模块 | 路径 | 功能 |
|------|------|------|
| 💬 多模态答疑 | `/chat` | 文字/图片提问，Markdown+KaTeX 渲染，追问模式，深度模式，对话历史侧栏 |
| 📝 AI 错题本 | `/errorbook` | 按科目分组展示，复习状态管理，AI 生成变式题 |
| ✏️ 智能刷题 | `/practice` | 按科目/难度选题，提交答案，正确率统计，错题自动入库 |
| 🔬 虚拟实验室 | `/lab` | 嵌入 PhET 仿真，8+ 交互实验，使用时长自动记录 |
| 📊 学情分析 | `/analysis` | ECharts 雷达图，薄弱知识点识别，AI 学习建议 |
| 📅 学习历程 | `/journey` | 日历热力图，活动时间轴，多类型活动聚合 |
| 🧠 知识图谱 | `/knowledge` | Canvas 力导向图，86 知识点节点，5 学科分色，掌握度展示，用户标记系统 |
| ✍️ 知识点贡献 | `/contribute` | 用户提交新知识点，管理员审核，三标签页面（提价/我的贡献/审核管理）|

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3 (Composition API) + Vite + Pinia + Vue Router + ECharts + KaTeX |
| 后端 | FastAPI + Uvicorn + aiosqlite + Pydantic |
| AI | Mimo API + DeepSeek V4 Pro API |
| 部署 | Vercel (前端) + Railway (后端) |
| 设计 | 深墨蓝+琥珀色系，玻璃质感，Luminous Scholarly 设计系统 |

---

## 项目结构

```
WooStudy/
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── main.py              # 入口 + CORS + 路由注册
│   │   ├── config.py            # 环境变量配置
│   │   ├── routers/             # 路由层（chat/errorbook/practice/lab/analysis/knowledge/auth/settings）
│   │   ├── services/            # 业务逻辑层
│   │   ├── ai/                  # AI 集成层（dispatcher + mimo/deepseek/mock client）
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   └── db/                  # SQLite 数据库（连接管理 + 建表迁移）
│   ├── seed_data/               # 种子数据（题库 + 知识图谱）
│   ├── .env.example
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.json
│
├── frontend/                    # Vue3 前端
│   ├── src/
│   │   ├── views/               # 9 个页面组件
│   │   ├── api/                 # API 客户端
│   │   ├── stores/              # Pinia 状态管理（auth/user/chat）
│   │   ├── router/              # 路由配置 + 导航守卫
│   │   ├── assets/styles/       # 全局 CSS 设计系统
│   │   ├── constants/           # 共享常量（科目列表、storage key）
│   │   └── utils/               # 工具函数（KaTeX 渲染、图片压缩）
│   ├── vite.config.js
│   ├── vercel.json
│   └── package.json
│
└── README.md
```

---

## 本地运行

### 1. 后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 确保 .env 已配置
# 默认 Mock 模式，不消耗真实 API 配额

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

后端运行在 `http://localhost:8000`  
API 文档：`http://localhost:8000/docs`（Swagger UI）

### 2. 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行在 `http://localhost:5173`，Vite 自动代理 `/api` 到后端 8000 端口。

---

## 用户认证流程

1. **注册**：用户名 + 密码 + Mimo Key + DeepSeek Key → pbkdf2 哈希 → JWT（7天有效）
2. **登录**：用户名 + 密码 → 验证 pbkdf2 → 签发 JWT
3. **API Key 机制**：用户自备 Key，存储在服务端数据库；提问时从 DB 读取、不设服务器备用 Key
4. **角色权限**：user / contributor / admin（管理员通过 `ADMIN_USERNAME` 环境变量设置）

---

## 双模型调度逻辑

```
用户输入 → 非物理话题 → Mimo Flash（廉价模型，关心鼓励）
         ↘ 物理话题 → Mimo(L1) → 置信度 ≥ 0.7 → 直接返回
                                 ↘ 置信度 < 0.7 → DeepSeek(L2) 深度回答
         ↘ 深度优先 → 跳过 Mimo，直达 DeepSeek
```

---

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| GET | `/api/auth/me` | 当前用户信息 |
| PUT | `/api/auth/api-keys` | 更新 API Key |
| POST | `/api/chat/send` | 发送文字消息 |
| POST | `/api/chat/upload` | 上传图片提问 |
| GET | `/api/chat/history` | 对话历史 |
| GET/POST/DELETE | `/api/chat/sessions` | 会话管理 |
| GET | `/api/errorbook` | 错题列表 |
| PUT | `/api/errorbook/{id}/review` | 标记已复习 |
| POST | `/api/errorbook/{id}/variant` | 生成变式题 |
| GET | `/api/practice` | 获取刷题 |
| POST | `/api/practice/submit` | 提交答案 |
| GET | `/api/lab/list` | 实验列表 |
| POST | `/api/lab/session` | 记录实验 |
| GET | `/api/analysis/report` | 学情报告 |
| GET | `/api/analysis/journey` | 学习历程 |
| GET/PUT | `/api/settings` | 用户设置 |
| GET | `/api/knowledge/graph` | 知识图谱（含掌握度） |
| POST/DELETE | `/api/knowledge/markers` | 用户标记管理 |
| CRUD | `/api/knowledge/nodes` | 管理员：节点 CRUD |
| CRUD | `/api/knowledge/edges` | 管理员：边 CRUD |
| POST | `/api/knowledge/contributions` | 用户提交知识点贡献 |
| GET/PUT | `/api/knowledge/pending` | 管理员：审核贡献 |

---

## 部署

### Railway（后端）

1. 连接 GitHub 仓库，选择 `backend/` 目录
2. 设置环境变量：`JWT_SECRET`（必填）、`ADMIN_USERNAME`（可选，自动设管理员）
3. Railway 自动识别 `Dockerfile` 构建部署

### Vercel（前端）

1. 连接 GitHub 仓库，选择 `frontend/` 目录
2. 设置环境变量：`VITE_API_BASE` → 后端地址
3. 框架预设选择 **Vite**

---

## 设计系统

v4 Luminous Scholarly — 深墨蓝 `#1B2A4A` + 琥珀色 `#D97706` + 暖白背景 `#F7F5F0`

- 渐变按钮、玻璃质感卡片、琥珀色焦点光晕
- 每页独立氛围色背景光晕（data-page 驱动）
- spring 动画曲线 + 入场序列微动效
- 磨砂标签组导航 + 移动端侧滑抽屉
- 响应式适配 + 触控优化
