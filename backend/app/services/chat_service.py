"""多模态答疑服务——对话记录管理 + AI 调度"""

import json
import base64
from pathlib import Path
from typing import Optional
from datetime import date

from app.ai.dispatcher import dispatch_chat, dispatch_followup_chat
from app.db.database import get_db
from app.config import get_settings
from app.services import get_user_api_keys


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

    await _ensure_session(db, session_id)

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

    await db.execute(
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
    await db.execute(
        "INSERT INTO chat_history (session_id, role, content, model_used, confidence) VALUES (?, ?, ?, ?, ?)",
        (session_id, "assistant", ai_result["content"], ai_result["model_used"], ai_result["confidence"]),
    )

    await db.execute(
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
    cursor = await db.execute(
        "SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT ?",
        (session_id, limit),
    )
    rows = await cursor.fetchall()
    await cursor.close()
    messages = [
        {"role": row["role"], "content": row["content"]}
        for row in reversed(rows)
    ]
    return {"messages": messages}


async def _save_learning_summary(db, session_id: str, summary: str) -> None:
    """保存今日学习摘要"""
    today = date.today().isoformat()
    cursor = await db.execute(
        "SELECT id, subjects_json, summary_text FROM learning_summaries WHERE session_id = ? AND date = ?",
        (session_id, today),
    )
    row = await cursor.fetchone()
    await cursor.close()

    if row:
        existing = row["summary_text"] or ""
        new_text = existing + "\n" + summary if existing else summary
        await db.execute(
            "UPDATE learning_summaries SET summary_text = ?, updated_at = datetime('now') WHERE id = ?",
            (new_text[:1000], row["id"]),
        )
    else:
        await db.execute(
            "INSERT INTO learning_summaries (session_id, date, summary_text) VALUES (?, ?, ?)",
            (session_id, today, summary[:1000]),
        )


async def get_history(session_id: str, limit: int = 50) -> dict:
    """获取对话历史"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, role, content, image_url, model_used, created_at "
        "FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT ?",
        (session_id, limit),
    )
    rows = await cursor.fetchall()
    await cursor.close()
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


async def _ensure_session(db, session_id: str) -> None:
    """如果 session 不存在则创建"""
    cursor = await db.execute("SELECT id FROM sessions WHERE session_id = ?", (session_id,))
    row = await cursor.fetchone()
    await cursor.close()
    if row is None:
        await db.execute("INSERT INTO sessions (session_id) VALUES (?)", (session_id,))
        await db.commit()
