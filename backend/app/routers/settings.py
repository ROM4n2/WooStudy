"""用户设置路由——读取和更新会话设置（deep_mode 等）"""

import json
from fastapi import APIRouter
from pydantic import BaseModel
from app.db.database import get_db

router = APIRouter(prefix="/api/settings", tags=["设置"])


class SettingsUpdate(BaseModel):
    settings: dict


@router.get("")
async def get_settings(session_id: str) -> dict:
    """获取用户设置"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT settings_json FROM sessions WHERE session_id = ?",
        (session_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()

    if row is None:
        return {"settings": {"deep_mode": False}}

    settings = json.loads(row["settings_json"]) if row["settings_json"] else {}
    return {"settings": settings}


@router.put("")
async def update_settings(session_id: str, body: SettingsUpdate) -> dict:
    """更新用户设置"""
    db = await get_db()

    # 确保 session 存在
    cursor = await db.execute("SELECT id FROM sessions WHERE session_id = ?", (session_id,))
    exists = await cursor.fetchone()
    await cursor.close()
    if not exists:
        await db.execute("INSERT INTO sessions (session_id) VALUES (?)", (session_id,))
        await db.commit()
        current = {}
    else:
        cursor = await db.execute(
            "SELECT settings_json FROM sessions WHERE session_id = ?",
            (session_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        current = json.loads(row["settings_json"]) if row and row["settings_json"] else {}
    current.update(body.settings)

    await db.execute(
        "UPDATE sessions SET settings_json = ?, updated_at = datetime('now') WHERE session_id = ?",
        (json.dumps(current, ensure_ascii=False), session_id),
    )
    await db.commit()

    return {"settings": current, "success": True}
