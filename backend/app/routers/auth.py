"""用户注册/登录/Key 管理路由"""

from fastapi import APIRouter, HTTPException, Depends
from app.db.database import get_db
from app.auth import hash_password, verify_password, create_token, get_current_user, require_user
from app.config import get_settings
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse, ApiKeyUpdate

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest) -> AuthResponse:
    """注册新用户（含 API Key）"""
    settings = get_settings()
    db = await get_db()

    # 检查用户名是否已存在
    cursor = await db.execute("SELECT id FROM users WHERE username = ?", (body.username,))
    if await cursor.fetchone():
        await cursor.close()
        raise HTTPException(status_code=409, detail="用户名已被使用")

    await cursor.close()

    # 创建用户
    pwd_hash = hash_password(body.password)
    cursor = await db.execute(
        """INSERT INTO users (username, password_hash, mimo_api_key, deepseek_api_key, has_api_keys)
           VALUES (?, ?, ?, ?, 1)""",
        (body.username, pwd_hash, body.mimo_api_key, body.deepseek_api_key),
    )
    await db.commit()
    user_id = cursor.lastrowid
    await cursor.close()

    token = create_token(user_id, body.username, settings.jwt_secret)
    return AuthResponse(token=token, user_id=user_id, username=body.username, has_api_keys=True)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest) -> AuthResponse:
    """登录验证"""
    settings = get_settings()
    db = await get_db()

    cursor = await db.execute(
        "SELECT id, username, password_hash, has_api_keys FROM users WHERE username = ?",
        (body.username,),
    )
    row = await cursor.fetchone()
    await cursor.close()

    if not row:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_token(row["id"], row["username"], settings.jwt_secret)
    return AuthResponse(
        token=token,
        user_id=row["id"],
        username=row["username"],
        has_api_keys=bool(row["has_api_keys"]),
    )


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    user = require_user(user)
    settings = get_settings()
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, username, has_api_keys FROM users WHERE id = ?",
        (user["user_id"],),
    )
    row = await cursor.fetchone()
    await cursor.close()

    if not row:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "user_id": row["id"],
        "username": row["username"],
        "has_api_keys": bool(row["has_api_keys"]),
        "mimo_invite_code": settings.mimo_invite_code,
    }


@router.put("/keys")
async def update_api_keys(body: ApiKeyUpdate, user: dict = Depends(get_current_user)):
    """更新用户的 API Key"""
    user = require_user(user)

    db = await get_db()
    has_keys = 1 if body.mimo_api_key and body.deepseek_api_key else 0

    await db.execute(
        """UPDATE users SET mimo_api_key = ?, deepseek_api_key = ?, has_api_keys = ?
           WHERE id = ?""",
        (body.mimo_api_key, body.deepseek_api_key, has_keys, user["user_id"]),
    )
    await db.commit()

    return {"success": True, "has_api_keys": bool(has_keys)}
