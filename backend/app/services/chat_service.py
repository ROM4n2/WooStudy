"""多模态答疑服务——对话记录管理 + AI 调度"""

import json
import base64
from pathlib import Path
from typing import Optional
from datetime import date, datetime, timedelta

from app.ai.dispatcher import dispatch_chat, dispatch_followup_chat
from app.db.database import get_db, db_execute, db_fetch_all, db_fetch_one, parse_sqlite_date
from app.config import get_settings
from app.services import get_user_api_keys


async def list_sessions(user_id: Optional[int] = None, session_ids: Optional[list[str]] = None) -> dict:
    """列出会话，按日期分组（今天、昨天、本周、更早）"""
    today = date.today()
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())

    if user_id:
        rows = await db_fetch_all(
            "SELECT session_id, title, created_at, updated_at FROM sessions "
            "WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        )
    elif session_ids:
        placeholders = ",".join("?" for _ in session_ids)
        rows = await db_fetch_all(
            f"SELECT session_id, title, created_at, updated_at FROM sessions "
            f"WHERE session_id IN ({placeholders}) ORDER BY updated_at DESC",
            session_ids,
        )
    else:
        return {"groups": {}}

    groups = {"今天": [], "昨天": [], "本周": [], "更早": []}
    for row in rows:
        updated = parse_sqlite_date(row["updated_at"]) or today
        session_data = {
            "session_id": row["session_id"],
            "title": row["title"] or "新对话",
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        if updated == today:
            groups["今天"].append(session_data)
        elif updated == yesterday:
            groups["昨天"].append(session_data)
        elif updated >= week_start:
            groups["本周"].append(session_data)
        else:
            groups["更早"].append(session_data)

    # 去掉空分组
    return {"groups": {k: v for k, v in groups.items() if v}}


async def create_session(session_id: str, user_id: Optional[int] = None) -> dict:
    """创建新会话"""
    db = await get_db()
    await db_execute(
        "INSERT OR IGNORE INTO sessions (session_id, user_id, title, updated_at) VALUES (?, ?, ?, datetime('now'))",
        (session_id, user_id, "新对话"),
    )
    await db.commit()
    return {"session_id": session_id, "title": "新对话"}


async def delete_session(session_id: str, user_id: Optional[int] = None) -> bool:
    """删除会话及其所有消息"""
    db = await get_db()
    # 验证归属
    if user_id:
        row = await db_fetch_one(
            "SELECT id FROM sessions WHERE session_id = ? AND user_id = ?", (session_id, user_id)
        )
    else:
        row = await db_fetch_one(
            "SELECT id FROM sessions WHERE session_id = ?", (session_id,)
        )
    if not row:
        return False

    await db_execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
    await db_execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    await db.commit()
    return True


async def _auto_set_title(db, session_id: str, first_content: str) -> None:
    """从第一条用户消息自动生成会话标题"""
    title = first_content.strip()[:30] if first_content.strip() else "图片提问"
    await db_execute(
        "UPDATE sessions SET title = ? WHERE session_id = ? AND (title IS NULL OR title = '新对话')",
        (title, session_id),
    )


async def send_message(
    session_id: str,
    content: str,
    user_id: int = 0,
    image_data: Optional[bytes] = None,
    deep_mode: bool = False,
    follow_up: bool = False,
) -> dict:
    """处理用户消息：保存记录 → 调用 AI → 保存回答 → 返回"""
    db = await get_db()
    settings = get_settings()

    await _ensure_session(db, session_id, user_id if user_id else None, content)

    # 保存用户消息
    image_url = None
    if image_data:
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        import uuid
        filename = f"{uuid.uuid4().hex}.jpg"
        file_path = upload_dir / filename
        file_path.write_bytes(image_data)
        image_url = f"/uploads/{filename}"

    await db_execute(
        "INSERT INTO chat_history (session_id, role, content, image_url) VALUES (?, ?, ?, ?)",
        (session_id, "user", content or "(图片)", image_url),
    )

    # 获取用户 API Key
    keys = await get_user_api_keys(user_id) if user_id else {"mimo_key": "", "deepseek_key": ""}

    # 调用 AI 调度器
    image_base64 = base64.b64encode(image_data).decode("utf-8") if image_data else None

    if follow_up and not image_data:
        history = await get_recent_messages(db, session_id)
        ai_result = await dispatch_followup_chat(
            history=history["messages"],
            new_content=content,
            deep_mode=deep_mode,
            mimo_key=keys["mimo_key"],
            deepseek_key=keys["deepseek_key"],
        )
        await _save_learning_summary(db, session_id, ai_result.get("summary_for_persist", ""))
    else:
        ai_result = await dispatch_chat(
            content=content,
            image_base64=image_base64,
            deep_mode=deep_mode,
            mimo_key=keys["mimo_key"],
            deepseek_key=keys["deepseek_key"],
        )

    # 保存 AI 回答
    await db_execute(
        "INSERT INTO chat_history (session_id, role, content, model_used, confidence) VALUES (?, ?, ?, ?, ?)",
        (session_id, "assistant", ai_result["content"], ai_result["model_used"], ai_result["confidence"]),
    )

    await db_execute(
        "UPDATE sessions SET updated_at = datetime('now') WHERE session_id = ?",
        (session_id,),
    )
    await db.commit()

    full_history = await get_history(session_id)
    return {
        "content": ai_result["content"],
        "model_used": ai_result["model_used"],
        "confidence": ai_result["confidence"],
        "history": full_history["messages"],
    }


async def get_recent_messages(db, session_id: str, limit: int = 10) -> dict:
    """获取最近对话（用于追问上下文）"""
    rows = await db_fetch_all(
        "SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT ?",
        (session_id, limit),
    )
    messages = [
        {"role": row["role"], "content": row["content"]}
        for row in reversed(rows)
    ]
    return {"messages": messages}


async def _save_learning_summary(db, session_id: str, summary: str) -> None:
    """保存今日学习摘要"""
    today = date.today().isoformat()
    row = await db_fetch_one(
        "SELECT id, subjects_json, summary_text FROM learning_summaries WHERE session_id = ? AND date = ?",
        (session_id, today),
    )

    if row:
        existing = row["summary_text"] or ""
        new_text = existing + "\n" + summary if existing else summary
        await db_execute(
            "UPDATE learning_summaries SET summary_text = ?, updated_at = datetime('now') WHERE id = ?",
            (new_text[:1000], row["id"]),
        )
    else:
        await db_execute(
            "INSERT INTO learning_summaries (session_id, date, summary_text) VALUES (?, ?, ?)",
            (session_id, today, summary[:1000]),
        )


async def get_history(session_id: str, limit: int = 50) -> dict:
    """获取对话历史"""
    rows = await db_fetch_all(
        "SELECT id, role, content, image_url, model_used, created_at "
        "FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT ?",
        (session_id, limit),
    )
    messages = [
        {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "image_url": row["image_url"],
            "model_used": row["model_used"],
            "created_at": row["created_at"],
        }
        for row in reversed(rows)
    ]
    return {"messages": messages, "total": len(messages)}


async def _ensure_session(db, session_id: str, user_id: Optional[int] = None, content: str = "") -> None:
    """如果 session 不存在则创建，并从首条消息自动命名"""
    row = await db_fetch_one("SELECT id FROM sessions WHERE session_id = ?", (session_id,))
    if row is None:
        title = content.strip()[:30] if content.strip() else "新对话"
        await db_execute(
            "INSERT INTO sessions (session_id, user_id, title) VALUES (?, ?, ?)",
            (session_id, user_id, title),
        )
        await db.commit()
