"""用户认证模块：密码哈希、JWT 签发/验证、FastAPI 依赖注入"""

import hashlib
import os
import time
from fastapi import Header, HTTPException
import jwt as pyjwt

# ── 密码哈希 ──
# 使用 hashlib.pbkdf2_hmac + 随机 salt，零额外依赖
HASH_ALGO = "sha256"
HASH_ITERATIONS = 600_000
HASH_SALT_LEN = 32
TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """返回格式: pbkdf2$sha256$iterations$salt_hex$hash_hex"""
    salt = os.urandom(HASH_SALT_LEN)
    pwd_hash = hashlib.pbkdf2_hmac(HASH_ALGO, password.encode(), salt, HASH_ITERATIONS)
    return f"pbkdf2${HASH_ALGO}${HASH_ITERATIONS}${salt.hex()}${pwd_hash.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """验证密码与存储哈希是否匹配"""
    try:
        parts = stored.split("$")
        if parts[0] != "pbkdf2":
            return False
        algo = parts[1]
        iterations = int(parts[2])
        salt = bytes.fromhex(parts[3])
        stored_hash = parts[4]
        pwd_hash = hashlib.pbkdf2_hmac(algo, password.encode(), salt, iterations)
        return pwd_hash.hex() == stored_hash
    except (IndexError, ValueError):
        return False


# ── JWT ──

def create_token(user_id: int, username: str, secret: str) -> str:
    """签发 JWT token，有效期 7 天"""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": int(time.time()) + TOKEN_EXPIRE_DAYS * 86400,
        "iat": int(time.time()),
    }
    return pyjwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> dict | None:
    """解码 JWT token，失败返回 None"""
    try:
        return pyjwt.decode(token, secret, algorithms=["HS256"])
    except pyjwt.PyJWTError:
        return None


# ── FastAPI 依赖注入 ──

async def get_current_user(
    authorization: str = Header(default=""),
) -> dict | None:
    """从 Authorization header 提取并验证 JWT，返回 { user_id, username }

    作为 FastAPI Depends 使用：Depends(get_current_user)
    未认证时返回 None，路由自行检查。
    """
    from app.config import get_settings
    settings = get_settings()

    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    payload = decode_token(token, settings.jwt_secret)
    if payload is None:
        return None

    return {"user_id": payload["user_id"], "username": payload["username"]}


def require_user(user: dict | None) -> dict:
    """在路由中调用，确保用户已认证"""
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return user
