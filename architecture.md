# 物知学 — 项目架构设计

## 一、总体架构图

```
┌─────────────────────────────────────────────────────┐
│                   用户浏览器                           │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐  │
│  │ 答疑/拍题 │ │  错题本   │ │ 智能刷题│ │虚拟实验室│  │
│  └────┬─────┘ └────┬─────┘ └───┬────┘ └────┬─────┘  │
│       │            │           │           │         │
│  ┌────┴────────────┴───────────┴───────────┴────┐    │
│  │          API 客户端 (axios)                    │    │
│  └────────────────────┬──────────────────────────┘    │
└───────────────────────┼──────────────────────────────┘
                        │ HTTPS
                        ▼
┌──────────────────────────────────────────────────────┐
│              Railway (FastAPI + Uvicorn)              │
│                                                      │
│  ┌──────────┐  ┌──────────────────┐  ┌──────────┐   │
│  │  Router  │──│   Service Layer   │──│  Models  │   │
│  │  Layer   │  │  (业务逻辑)       │  │ (DB)    │   │
│  ├──────────┤  ├──────────────────┤  ├──────────┤   │
│  │ chat     │  │ ChatService      │  │ User     │   │
│  │ errorbook│  │ ErrorBookService │  │ Session  │   │
│  │ practice │  │ PracticeService  │  │ Question │   │
│  │ lab      │  │ LabService       │  │ ErrorLog │   │
│  │ analysis │  │ AnalysisService  │  │ Variant  │   │
│  └────┬─────┘  └────────┬─────────┘  │ LabSession│   │
│       │                 │            └─────┬─────┘   │
│       │         ┌───────┴────────┐         │         │
│       │         │ AI Dispatcher  │    ┌────┴─────┐   │
│       │         │  (双模型调度器) │    │  SQLite  │   │
│       │         ├────────────────┤    │ (aiosqlite)│  │
│       │         │ L1: Mimo       │    └──────────┘   │
│       │         │ L2: DeepSeek   │                    │
│       │         │ Mock: fallback │                    │
│       │         └───────┬────────┘                    │
│       └─────────────────┼────────────────────────────┘
│                         │
└─────────────────────────┼────────────────────────────┘
                          │ API calls
                          ▼
              ┌─────────────────────┐
              │  Mimo API (识图+简答) │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │ DeepSeek V4 Pro API  │
              │ (深度答疑+变式+学情)   │
              └─────────────────────┘
```

## 二、后端项目结构 (FastAPI)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 入口，CORS，路由注册
│   ├── config.py                  # 环境变量加载（pydantic-settings）
│   │
│   ├── routers/                   # 路由层（仅做参数校验 + 调用 service）
│   │   ├── __init__.py
│   │   ├── chat.py                # POST /chat/send, POST /chat/upload
│   │   ├── errorbook.py           # GET/POST /errorbook, POST /errorbook/variant
│   │   ├── practice.py            # GET /practice, POST /practice/submit
│   │   ├── lab.py                 # GET /lab/list, POST /lab/session
│   │   └── analysis.py            # GET /analysis/report
│   │
│   ├── services/                  # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── chat_service.py        # 多模态答疑逻辑
│   │   ├── errorbook_service.py   # 错题本 CRUD + 变式生成
│   │   ├── practice_service.py    # 智能刷题逻辑
│   │   ├── lab_service.py         # 实验室会话记录
│   │   └── analysis_service.py    # 学情分析与雷达图数据
│   │
│   ├── ai/                        # AI 集成层
│   │   ├── __init__.py
│   │   ├── dispatcher.py          # L1→L2 调度器（置信度判断+fallback）
│   │   ├── mimo_client.py         # Mimo API 封装
│   │   ├── deepseek_client.py     # DeepSeek API 封装
│   │   └── mock_client.py         # Mock 实现（开发阶段替代真实调用）
│   │
│   ├── models/                    # SQLite 数据库模型
│   │   ├── __init__.py
│   │   ├── base.py                # 基类（通用字段 created_at, updated_at）
│   │   ├── user.py                # 用户表（预留，MVP 暂用 session）
│   │   ├── session.py             # 匿名 session 表
│   │   ├── question.py            # 题库表
│   │   ├── chat_history.py        # 对话记录表
│   │   ├── error_log.py           # 错题本表
│   │   ├── variant_question.py    # 变式题记录表
│   │   └── lab_session.py         # 仿真实验室会话表
│   │
│   ├── schemas/                   # Pydantic 请求/响应模型
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── errorbook.py
│   │   ├── practice.py
│   │   ├── lab.py
│   │   └── analysis.py
│   │
│   └── db/
│       ├── __init__.py
│       ├── database.py            # SQLite 连接 + 初始化
│       └── migrate.py             # 建表/迁移脚本
│
├── seed_data/
│   └── questions.json             # DeepSeek 生成的种子题目
│
├── .env.example                   # 环境变量模板
├── requirements.txt
├── railway.json                   # Railway 部署配置
└── Dockerfile
```

## 三、前端项目结构 (Vue3 + Vite)

```
frontend/
├── src/
│   ├── App.vue
│   ├── main.js
│   ├── router/
│   │   └── index.js               # Vue Router 配置
│   │
│   ├── api/
│   │   ├── request.js             # axios 实例（baseURL, 拦截器）
│   │   ├── chat.js                # 答疑相关 API
│   │   ├── errorbook.js           # 错题本 API
│   │   ├── practice.js            # 刷题 API
│   │   ├── lab.js                 # 实验室 API
│   │   └── analysis.js            # 学情分析 API
│   │
│   ├── views/
│   │   ├── AccessGate.vue          # 访问密码门禁页
│   │   ├── ChatView.vue           # 聊天/拍题页（含图片上传）
│   │   ├── ErrorBookView.vue      # 错题本页（分组+变式出题按钮）
│   │   ├── PracticeView.vue       # 智能刷题页（题目+答案对比）
│   │   ├── LabView.vue            # 虚拟实验室页（PhET iframe）
│   │   └── AnalysisView.vue       # 学情分析页（雷达图+报告）
│   │
│   ├── components/
│   │   ├── ImageUploader.vue       # 图片上传组件（压缩 + 预览）
│   │   ├── ChatBubble.vue         # 对话气泡组件
│   │   ├── QuestionCard.vue       # 题目卡片组件
│   │   ├── VariantList.vue        # 变式题列表
│   │   ├── RadarChart.vue         # 雷达图 ECharts 组件
│   │   └── LoadingOverlay.vue     # 加载等待动画
│   │
│   ├── stores/                    # Pinia 状态管理
│   │   ├── chat.js
│   │   ├── errorbook.js
│   │   ├── practice.js
│   │   └── user.js
│   │
│   ├── utils/
│   │   ├── compress.js            # 前端图片压缩
│   │   └── format.js              # 格式化工具
│   │
│   └── assets/
│       └── styles/
│           └── main.css
│
├── public/
│   └── favicon.ico
│
├── index.html
├── vite.config.js
├── vercel.json                    # Vercel 部署配置
└── package.json
```

## 四、数据库 ER 关系

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────────┐
│   sessions   │     │  chat_history    │     │     questions      │
├──────────────┤     ├──────────────────┤     ├────────────────────┤
│ id (PK)      │────→│ id (PK)          │     │ id (PK)            │
│ session_id   │     │ session_id (FK)  │     │ content (题目内容)  │
│ created_at   │     │ question_text    │     │ options (JSON选项) │
│ updated_at   │     │ image_url (可选)  │     │ correct_answer     │
│ settings     │     │ ai_response      │     │ explanation        │
└──────────────┘     │ model_used       │     │ subject (力学/电学) │
                     │ confidence       │     │ difficulty (1-5)   │
                     │ created_at       │     │ tags (JSON)        │
                     └──────────────────┘     │ created_at         │
                                              └────────┬───────────┘
┌──────────────────┐     ┌────────────────────┐         │
│   error_logs     │     │ variant_questions  │         │
├──────────────────┤     ├────────────────────┤         │
│ id (PK)          │     │ id (PK)            │         │
│ session_id (FK)  │────→│ error_log_id (FK)  │         │
│ question_id (FK) │     │ content (变式题目)   │◄────────┘
│ user_answer      │     │ options (JSON)     │
│ is_correct       │     │ correct_answer     │
│ wrong_reason     │     │ user_answer        │
│ subject          │     │ is_correct         │
│ created_at       │     │ generated_by       │
│ reviewed(已复习)  │     │ created_at         │
└──────────────────┘     └────────────────────┘

┌─────────────────────┐    ┌─────────────────────┐
│   lab_sessions      │    │   analysis_cache    │
├─────────────────────┤    ├─────────────────────┤
│ id (PK)             │    │ id (PK)             │
│ session_id (FK)     │    │ session_id (FK)     │
│ lab_name (PhET ID)  │    │ report_data (JSON)  │
│ started_at          │    │ generated_at        │
│ ended_at            │    └─────────────────────┘
│ duration_seconds    │
└─────────────────────┘
```

## 五、API 路由一览

| 模块 | 方法 | 路径 | 描述 |
|------|------|------|------|
| 答疑 | POST | `/api/chat/send` | 发送文字消息 |
| 答疑 | POST | `/api/chat/upload` | 上传图片并提问 |
| 答疑 | GET | `/api/chat/history` | 获取对话历史 |
| 错题本 | GET | `/api/errorbook` | 获取错题列表（支持分组） |
| 错题本 | PUT | `/api/errorbook/{id}/review` | 标记已复习 |
| 错题本 | POST | `/api/errorbook/{id}/variant` | 生成变式题 |
| 刷题 | GET | `/api/practice` | 获取推荐题目 |
| 刷题 | POST | `/api/practice/submit` | 提交答案 |
| 实验室 | GET | `/api/lab/list` | 获取可用实验列表 |
| 实验室 | POST | `/api/lab/session` | 记录实验会话 |
| 学情 | GET | `/api/analysis/report` | 获取学情分析报告 |
| 设置 | GET | `/api/settings` | 获取用户设置 |
| 设置 | PUT | `/api/settings` | 更新用户设置 |

## 六、AI 调度逻辑 (Dispatcher)

```
用户请求
    │
    ▼
┌─────────────────────────────┐
│  判断是否需要识图？          │
│  (请求带 image 参数)         │
└──────┬──────────────────────┘
       │
   ┌───┴───┐
   │  是   │   否
   └───┬───┘
       ▼
┌──────────────────┐
│  Mimo: 多模态识图  │
│  (图片+文字→回答)  │
└──────┬───────────┘
       │
       ▼
┌───────────────────────────────┐
│  Mimo 置信度 ≥ 0.7?            │
│  或用户已开启"深度优先模式"?    │
└──────┬────────────────────────┘
   ┌───┴───┐
   │  是   │   否
   └───┬───┘
       ▼
┌──────────────────┐     ┌──────────┐
│  DeepSeek: 深度回答│     │ 返回 Mimo│
│  (推理+公式+步骤)  │     │  结果    │
└──────┬───────────┘     └──────────┘
       │
       ▼
┌──────────────────┐
│  返回 DeepSeek   │
│  结果 + 置信度    │
└──────────────────┘
```

## 七、部署拓扑

```
                        ┌──────────┐
                        │  Vercel   │
                        │ (Frontend)│
                        │ Vue3 SPA  │
                        │ 静态文件   │
                        └────┬─────┘
                             │ /api/* 反向代理
                             ▼
                        ┌──────────┐
                        │ Railway   │
                        │ (Backend) │
                        │ FastAPI   │
                        │ + SQLite  │
                        └──────────┘
```

SQLite 存储在 Railway 的持久卷（或临时存储，因 Railway 磁盘 ephemeral，需后续考虑迁移到 Turso 或 Supabase 等远程数据库。MVP 阶段可接受重启丢失历史数据以外的内容，我会把 seed_data 做成每次启动自动导入）。

---

以上就是完整的项目架构。看看有没有需要调整的地方？没问题的话，我下一步就开始写代码了，顺序是：

1. **后端骨架**：config → database → models → schemas → routers → services → AI dispatcher
2. **前端骨架**：router → api client → views → components
3. **种子数据 + 部署配置**
4. **README**
