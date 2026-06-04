# WooStudy — 高中物理 AI 助学平台

## 项目概览
计算机专业学生独立开发的高中物理 AI 助学 Web 项目。
学生用户在 Vercel 前端注册时自带 Mimo + DeepSeek API Key，不设服务器备用 Key。

## 技术栈
- **前端**：Vue 3 (Composition API + Pinia) + Vite + ECharts + KaTeX
- **后端**：FastAPI + aiosqlite + Pydantic
- **部署**：前端 Vercel，后端 Railway
- **AI**：Mimo (L1 多模态/基础) + DeepSeek V4 Pro (L2 深度推理)

## 项目路径
`d:\Code\物知学\`

## 关键文件结构

### 后端 (`backend/app/`)
- `main.py` — FastAPI 入口，注册路由 + CORS + 生命周期
- `config.py` — Pydantic Settings，从环境变量加载所有配置
- `auth.py` — pbkdf2 密码哈希 + JWT 签发/验证 + FastAPI Depends
- `ai/dispatcher.py` — 双模型调度：非物理话题→Flash、Mock、Mimo L1→DeepSeek L2 fallback
- `ai/mimo_client.py` — Mimo API 封装（mimo_chat / mimo_flash_chat）
- `ai/deepseek_client.py` — DeepSeek API 封装
- `ai/mock_client.py` — 开发阶段 Mock 数据
- `services/` — 业务逻辑层（chat/errorbook/practice/lab/analysis）
- `routers/` — API 路由层
- `schemas/` — Pydantic 请求/响应模型
- `db/` — SQLite 数据库连接 + 建表迁移

### 前端 (`frontend/src/`)
- `App.vue` — 导航栏 + 设置面板 + 路由出口
- `router/index.js` — Vue Router 配置 + 导航守卫
- `stores/auth.js` — 认证状态管理（Pinia）
- `api/request.js` — axios 实例，统一 baseURL + JWT 拦截
- `views/` — 页面组件
  - `ChatView.vue` — 多模态答疑（含追问/深度模式、打字动画、时间戳）
  - `ErrorBookView.vue` — 错题本（分组/筛选/复习/变式题）
  - `PracticeView.vue` — 智能刷题（科目/难度/进度/正确率）
  - `LabView.vue` — 虚拟实验室（PhET iframe）
  - `AnalysisView.vue` — 学情分析（ECharts 雷达图 + 薄弱点 + AI建议）
  - `JourneyView.vue` — 学习历程（热力图 + 活动时间轴）
  - `LoginView.vue` — 登录/注册（含邀请码弹窗）

## 部署
- **前端**：`https://woo-study.vercel.app`（GitHub 推送自动部署）
- **后端**：`https://woostudy-production.up.railway.app`（Docker 部署）
- **前端 API 地址**：`request.js` 中兜底指向 `https://woostudy-production.up.railway.app/api`
- **CORS**：允许 `http://localhost:5173` 和 `https://woo-study.vercel.app`

## 用户认证流程
1. 注册：用户名 + 密码 + Mimo Key + DeepSeek Key → pbkdf2 哈希 → JWT 7天
2. 登录：用户名 + 密码 → 验证 pbkdf2 → 签发 JWT
3. 提问：前端 Bearer token → auth.py 验证 → DB 读 Key → AI dispatcher

## 双模型调度逻辑
```
dispatch_chat(content, image_base64, deep_mode, mimo_key, deepseek_key)
├─ 非物理话题 → mimo_flash_chat（廉价模型，关心鼓励）
├─ Mock 模式 → mock_chat / mock_deepseek
├─ 深度模式 → deepseek_chat
└─ 标准模式 → mimo_chat（置信度 < 0.7 时 fallback 到 deepseek_chat）
```

## 关键业务规则
- 用户必须自带 API Key，**不设服务器备用 Key**
- `MOCK_MODE` 不设置时默认 `false`，走真实 AI
- 所有 API 路由前缀 `/api/`（前端 baseURL 自带）
- Railway 需要设 `JWT_SECRET` 环境变量

## 已实现
- [x] A. 对话历史侧栏（聊天记录按日期分组）— 2026-06-04
  - 多 session 管理（新建/切换/删除）
  - 侧栏按日期分组（今天/昨天/本周/更早）
  - 自动从首条消息命名对话标题
  - 移动端滑出式侧栏
- [x] 知识图谱可视化 — 2026-06-04
  - Canvas 力导向图渲染，86 个知识点节点
  - 学科分色发光节点（力学/电学/热学/光学/近代物理）
  - 粒子流边动画，薄弱知识点红色脉动
  - 缩放/拖拽/点击信息卡片（含掌握度进度条）
  - 深空背景，导航栏「图谱」入口
  - seed_data/knowledge_graph.json 结构化数据
  - DB 持久化 knowledge_nodes/edges/markers 三张表
  - 管理员 CRUD 接口（nodes + edges）
  - 用户标记系统（收藏/薄弱/重点），右键菜单 + 信息卡片切换
  - 掌握度算法增强：错题库 + 用户标记 + 学情摘要加权
  - 角色权限 admin/contributor/user

## 待做（按推荐顺序）
- [ ] 迁移阿里云（Railway + Vercel → 阿里云国内服务器）
  - 架构：Nginx 反代前端静态文件 + FastAPI 后端 + SQLite，单机无 Docker
  - 预算：~107 元/年（ECS t6 38~99 元 + 域名 .xyz 8 元）
  - 代码零改动：全由环境变量 /opt/woostudy/.env 驱动
  - 耗时大头：ICP 备案 10-20 个工作日
  - 期间可用 IP 测试，Vercel+Railway 保持并行
  - 详细方案见 `C:\Users\席皓宇\.claude\projects\D--Code\memory\aliyun_migration.md`
- [ ] 讨论区 + 资源共享（依赖阿里云稳定部署）
- [ ] 知识点上传接口 ✅（已实现为管理员 CRUD，待完善为贡献者流程）
