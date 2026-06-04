"""SQLite 数据库连接管理——使用 aiosqlite 异步驱动"""

import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import get_settings

# 全局连接池（SQLite 单连接即可，aiosqlite 是线程安全的）
_db_conn: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """获取当前数据库连接（首次调用时自动初始化）"""
    global _db_conn
    if _db_conn is None:
        settings = get_settings()
        db_path = Path(settings.database_url.replace("sqlite+aiosqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _db_conn = await aiosqlite.connect(str(db_path))
        _db_conn.row_factory = aiosqlite.Row
        # 启用 WAL 模式提升并发读性能
        await _db_conn.execute("PRAGMA journal_mode=WAL")
        await _db_conn.execute("PRAGMA foreign_keys=ON")
    return _db_conn


async def close_db() -> None:
    """关闭数据库连接（应用关闭时调用）"""
    global _db_conn
    if _db_conn:
        await _db_conn.close()
        _db_conn = None


@asynccontextmanager
async def get_db_cursor():
    """便捷的游标上下文管理器，自动提交/回滚"""
    db = await get_db()
    cursor = await db.cursor()
    try:
        yield cursor
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await cursor.close()
