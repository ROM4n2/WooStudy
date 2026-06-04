"""Service 层工具函数"""

from app.db.database import get_db


async def get_user_api_keys(user_id: int) -> dict:
    """从 users 表读取用户的 API Key"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT mimo_api_key, deepseek_api_key, has_api_keys FROM users WHERE id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    if not row or not row["has_api_keys"]:
        return {"mimo_key": "", "deepseek_key": ""}
    return {
        "mimo_key": row["mimo_api_key"] or "",
        "deepseek_key": row["deepseek_api_key"] or "",
    }
