# 📘 物知学 — 高中物理 AI 助学

> 基于 Vue3 + FastAPI + SQLite 的高中物理 AI 助学 Web 应用。  
> 含多模态答疑、AI 错题本、智能刷题、虚拟仿真实验室四大模块。  
> 双模型架构：Mimo（L1 识图简答）+ DeepSeek V4 Pro（L2 深度推理）。

---

## 项目结构

```
物知学/
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── main.py              # 入口 + CORS + 路由注册
│   │   ├── config.py            # 环境变量配置
│   │   ├── routers/             # 路由层
│   │   ├── services/            # 业务逻辑层
│   │   ├── ai/                  # AI 集成层（调度器 + API 封装）
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   └── db/                  # SQLite 数据库
│   ├── seed_data/
│   │   └── questions.json       # 30 道初始物理题
│   ├── .env.example             # 环境变量模板
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.json
│
├── frontend/                    # Vue3 前端
│   ├── src/
│   │   ├── views/               # 页面组件
│   │   ├── components/          # 通用组件
│   │   ├── api/                 # API 客户端
│   │   ├── stores/              # Pinia 状态管理
│   │   ├── router/              # 路由
│   │   └── utils/               # 工具函数
│   ├── vite.config.js
│   ├── vercel.json
│   └── package.json
│
├── architecture.md              # 完整架构文档
└── README.md
```

---

## 本地运行

### 1. 后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 确保 .env 已配置（项目已附带 .env，默认 Mock 模式）
# 如需切换真实 API，修改 .env 中的 MOCK_MODE=false

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

前端运行在 `http://localhost:5173`

---

## Mock 模式 vs 真实 API

| 模式 | .env 配置 | AI 响应 | API 消耗 |
|------|-----------|---------|---------|
| **Mock** | `MOCK_MODE=true`（默认） | 本地生成假数据，即时响应 | ❌ 不消耗 |
| **真实** | `MOCK_MODE=false` | 调用 Mimo + DeepSeek | ✅ 消耗配额 |

开发阶段建议使用 Mock 模式，所有功能正常运行但不产生 API 费用。  
切换到真实模式后，L1→L2 调度逻辑自动生效。

---

## 双模型调度逻辑

```
用户输入 → Mimo(L1) → 置信度 ≥ 0.7 → 直接返回
                      ↘ 置信度 < 0.7 → DeepSeek(L2) 深度回答
                      
用户开启"深度优先" → 跳过 Mimo，直达 DeepSeek
```

---

## 四大模块

| 模块 | 路径 | 功能 |
|------|------|------|
| 💬 多模态答疑 | `/chat` | 文字提问 + 图片上传（最多2张），AI 图文回答 |
| 📝 AI 错题本 | `/errorbook` | 按科目分组展示，变式出题，复习状态管理 |
| ✏️ 智能刷题 | `/practice` | 按科目/难度选题，提交答案 + 错题自动收录 |
| 🔬 虚拟实验室 | `/lab` | 嵌入 PhET 仿真，8 个交互实验（力学/电学/光学） |
| 📊 学情分析 | `/analysis` | 雷达图 + 薄弱知识点 + AI 学习建议 |

---

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/chat/send` | 发送文字消息 |
| POST | `/api/chat/upload` | 上传图片提问 |
| GET | `/api/chat/history` | 对话历史 |
| GET | `/api/errorbook` | 错题列表 |
| PUT | `/api/errorbook/{id}/review` | 标记已复习 |
| POST | `/api/errorbook/{id}/variant` | 生成变式题 |
| GET | `/api/practice` | 获取刷题 |
| POST | `/api/practice/submit` | 提交答案 |
| GET | `/api/lab/list` | 实验列表 |
| POST | `/api/lab/session` | 记录实验 |
| GET | `/api/analysis/report` | 学情报告 |
| GET/PUT | `/api/settings` | 用户设置 |

---

## 部署

### Railway（后端）

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

1. 连接 GitHub 仓库，选择 `backend/` 目录
2. 在 Railway Dashboard 设置环境变量：

   | 变量 | 必填 | 说明 |
   |------|------|------|
   | `MIMO_API_KEY` | 否* | Mimo API 密钥 |
   | `DEEPSEEK_API_KEY` | 否* | DeepSeek API 密钥 |
   | `MOCK_MODE` | 否 | 设为 `true` 可不填 API Key，走模拟数据 |
   | `CORS_ORIGINS` | 否 | JSON 数组，默认含 Vercel 域名 |

   *\* 两个 API Key 至少填一个，或 `MOCK_MODE=true` 跳过*

3. Railway 自动识别 `Dockerfile` 构建部署
4. 部署后获得 Railway 域名（如 `https://wuzhixue-prod.up.railway.app`）

### Vercel（前端）

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

1. 连接 GitHub 仓库，选择 `frontend/` 目录
2. 在 Vercel Dashboard 设置环境变量：

   | 变量 | 必填 | 说明 |
   |------|------|------|
   | `VITE_API_BASE` | ✅ | Railway 后端地址（如 `https://wuzhixue-prod.up.railway.app`） |
   | `VITE_ACCESS_PASSWORD` | ✅ | 访问密码（小范围分享用） |

3. 框架预设选择 **Vite**
4. 部署后即可通过 Vercel 域名访问

> **注意：** 部署后 SQLite 数据存储在 Railway 临时磁盘中，重启后错题本/对话记录等数据会丢失。公开上线前需迁移到 Supabase 等远程数据库。

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3 (Composition API) + Vite + Pinia + Vue Router + ECharts |
| 后端 | FastAPI + Uvicorn + aiosqlite + Pydantic |
| AI | Mimo API + DeepSeek V4 Pro API |
| 部署 | Vercel (前端) + Railway (后端) |
