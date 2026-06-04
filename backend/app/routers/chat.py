"""多模态答疑路由"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.schemas.chat import ChatSendRequest
from app.services import chat_service
from app.ai.dispatcher import dispatch_optimize_prompt
from app.auth import get_current_user, require_user

router = APIRouter(prefix="/api/chat", tags=["答疑"])


class OptimizeRequest(BaseModel):
    text: str


# ── Session 管理 ──


@router.get("/sessions")
async def list_sessions(
    session_ids: Optional[str] = Query(None, description="匿名用户：逗号分隔的 session_id 列表"),
    user: dict = Depends(get_current_user),
) -> dict:
    """列出当前用户的会话，按日期分组（今天/昨天/本周/更早）"""
    uid = user.get("user_id") if user else None
    ids = session_ids.split(",") if session_ids else None
    result = await chat_service.list_sessions(user_id=uid, session_ids=ids)
    return JSONResponse(result)


class CreateSessionRequest(BaseModel):
    session_id: str


@router.post("/sessions")
async def create_session(
    body: CreateSessionRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    """创建新会话"""
    uid = user.get("user_id") if user else None
    result = await chat_service.create_session(body.session_id, uid)
    return JSONResponse(result)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """删除会话及其所有消息"""
    user = require_user(user)
    ok = await chat_service.delete_session(session_id, user["user_id"])
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return JSONResponse({"ok": True})


# ── 对话 ──


@router.post("/optimize")
async def optimize_prompt(body: OptimizeRequest, user: dict = Depends(get_current_user)) -> dict:
    """优化用户提问"""
    user = user or {}  # 可选认证
    result = await dispatch_optimize_prompt(body.text)
    return JSONResponse(result)


@router.post("/send")
async def send_message(
    session_id: str,
    body: ChatSendRequest,
    deep_mode: bool = False,
    follow_up: bool = False,
    user: dict = Depends(get_current_user),
) -> dict:
    """发送文字消息"""
    user = require_user(user)
    result = await chat_service.send_message(
        session_id=session_id,
        content=body.content,
        user_id=user["user_id"],
        deep_mode=deep_mode,
        follow_up=follow_up,
    )
    return JSONResponse(result)


@router.post("/upload")
async def upload_image(
    session_id: str = Form(...),
    content: str = Form(""),
    image: UploadFile = File(...),
    deep_mode: bool = Form(False),
    user: dict = Depends(get_current_user),
) -> dict:
    """上传图片并提问"""
    image_data = await image.read()
    if len(image_data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过 5MB")

    user = require_user(user)
    result = await chat_service.send_message(
        session_id=session_id,
        content=content,
        image_data=image_data,
        user_id=user["user_id"],
        deep_mode=deep_mode,
    )
    return JSONResponse(result)


@router.get("/history")
async def get_history(
    session_id: str,
    limit: int = 50,
) -> dict:
    """获取对话历史"""
    result = await chat_service.get_history(session_id, limit)
    return JSONResponse(result)
