"""建表和迁移脚本——应用启动时自动执行"""

import json
from pathlib import Path

from app.db.database import get_db


CREATE_TABLES_SQL = """
-- 用户表（替代匿名 session）
CREATE TABLE IF NOT EXISTS users (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    username         TEXT    NOT NULL UNIQUE,
    password_hash    TEXT    NOT NULL,
    mimo_api_key     TEXT    DEFAULT '',
    deepseek_api_key TEXT    DEFAULT '',
    has_api_keys     INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- 匿名用户会话表
CREATE TABLE IF NOT EXISTS sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT    NOT NULL UNIQUE,
    settings_json   TEXT    DEFAULT '{}',       -- {"deep_mode": false} 等
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- 对话历史表（多模态答疑模块）
CREATE TABLE IF NOT EXISTS chat_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT    NOT NULL REFERENCES sessions(session_id),
    role            TEXT    NOT NULL CHECK(role IN ('user', 'assistant')),
    content         TEXT    NOT NULL,            -- 文本内容（Markdown 格式）
    image_url       TEXT,                        -- 用户上传的图片路径（可选）
    model_used      TEXT,                        -- 'mimo' / 'deepseek' / 'mock'
    confidence      REAL,                        -- 回答置信度 0~1
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- 题库表
CREATE TABLE IF NOT EXISTS questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    content         TEXT    NOT NULL,            -- 题目内容（Markdown，支持 LaTeX $...$）
    question_type   TEXT    NOT NULL DEFAULT 'single_choice'
                            CHECK(question_type IN ('single_choice', 'multiple_choice', 'fill_blank', 'essay')),
    options_json    TEXT,                        -- JSON 数组：["A. xxx", "B. xxx", ...]
    correct_answer  TEXT    NOT NULL,            -- 正确答案
    explanation     TEXT,                        -- 解析
    subject         TEXT    NOT NULL,            -- '力学' / '电学' / '热学' / '光学' / '近代物理'
    difficulty      INTEGER NOT NULL DEFAULT 3 CHECK(difficulty BETWEEN 1 AND 5),
    tags_json       TEXT    DEFAULT '[]',
    source          TEXT    DEFAULT 'seed',      -- 'seed' / 'variant' / 'upload'
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- 错题本表
CREATE TABLE IF NOT EXISTS error_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT    NOT NULL REFERENCES sessions(session_id),
    question_id     INTEGER REFERENCES questions(id),
    user_answer     TEXT    NOT NULL,
    is_correct      INTEGER NOT NULL DEFAULT 0,  -- 0=错题 1=已做对
    wrong_reason    TEXT,                        -- 模型分析的错误原因
    subject         TEXT,
    reviewed        INTEGER NOT NULL DEFAULT 0,  -- 0=未复习 1=已复习
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- 变式题记录表
CREATE TABLE IF NOT EXISTS variant_questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    error_log_id    INTEGER NOT NULL REFERENCES error_logs(id) ON DELETE CASCADE,
    content         TEXT    NOT NULL,
    options_json    TEXT,
    correct_answer  TEXT    NOT NULL,
    user_answer     TEXT,
    is_correct      INTEGER,
    generated_by    TEXT    NOT NULL DEFAULT 'deepseek',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- 仿真实验室会话记录表
CREATE TABLE IF NOT EXISTS lab_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT    NOT NULL REFERENCES sessions(session_id),
    lab_name        TEXT    NOT NULL,            -- 实验标识（如 'pendulum-lab'）
    lab_title       TEXT,                        -- 实验中文名
    started_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    ended_at        TEXT,
    duration_seconds INTEGER
);

-- 学情分析缓存表
CREATE TABLE IF NOT EXISTS analysis_cache (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT    NOT NULL UNIQUE REFERENCES sessions(session_id),
    report_json     TEXT    NOT NULL,            -- 完整的学情分析报告（JSON）
    generated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- 学习摘要表（追问模式总结 + 个人化成长记录）
CREATE TABLE IF NOT EXISTS learning_summaries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT    NOT NULL REFERENCES sessions(session_id),
    date            TEXT    NOT NULL,                -- 日期，如 '2026-06-04'
    subjects_json   TEXT    DEFAULT '[]',            -- 涉及的知识点列表 ["力学", "电学"]
    summary_text    TEXT,                            -- 当日学习摘要
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(session_id, date)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_chat_session    ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_error_session   ON error_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_error_subject   ON error_logs(subject);
CREATE INDEX IF NOT EXISTS idx_variant_error   ON variant_questions(error_log_id);
CREATE INDEX IF NOT EXISTS idx_lab_session     ON lab_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_questions_subject ON questions(subject);
"""


async def init_db() -> None:
    """初始化数据库：建表 + 种子数据导入（首次启动）"""
    db = await get_db()
    # 逐条执行建表语句（aiosqlite 不支持多语句一次执行）
    for statement in CREATE_TABLES_SQL.split(";"):
        stmt = statement.strip()
        if stmt:
            await db.execute(stmt + ";")
    await db.commit()
    print("[DB] 数据库表结构初始化完成")

    # 运行增量迁移（新加字段）
    await _run_migrations(db)


async def _run_migrations(db) -> None:
    """增量迁移：给已有表加字段"""
    migrations = [
        ("ALTER TABLE sessions ADD COLUMN user_id INTEGER REFERENCES users(id)", "sessions.user_id"),
        ("ALTER TABLE sessions ADD COLUMN title TEXT DEFAULT '新对话'", "sessions.title"),
    ]
    for sql, desc in migrations:
        try:
            await db.execute(sql)
            await db.commit()
            print(f"[DB] 迁移完成：{desc}")
        except Exception:
            pass  # 字段已存在则忽略

    # 导入种子题目（如果题库为空）
    cursor = await db.execute("SELECT COUNT(*) FROM questions")
    row = await cursor.fetchone()
    if row[0] == 0:
        await _seed_questions(db)
    await cursor.close()


async def _seed_questions(db) -> None:
    """从 seed_data/questions.json 导入初始题库"""
    seed_path = Path(__file__).parent.parent.parent / "seed_data" / "questions.json"
    if not seed_path.exists():
        print("[DB] 未找到 seed_data/questions.json，跳过种子数据导入")
        return

    with open(seed_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    for q in questions:
        await db.execute(
            """INSERT INTO questions (content, question_type, options_json, correct_answer,
               explanation, subject, difficulty, tags_json, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                q["content"],
                q.get("question_type", "single_choice"),
                json.dumps(q.get("options", []), ensure_ascii=False),
                q["correct_answer"],
                q.get("explanation", ""),
                q["subject"],
                q.get("difficulty", 3),
                json.dumps(q.get("tags", []), ensure_ascii=False),
                "seed",
            ),
        )
    await db.commit()
    print(f"[DB] 已从 seed_data/questions.json 导入 {len(questions)} 道种子题目")
