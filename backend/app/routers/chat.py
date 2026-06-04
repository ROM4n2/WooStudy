"""多模态答疑路由"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.schemas.chat import ChatSendRequest
from app.services import chat_service
from app.ai.dispatcher import dispatch_optimize_prompt
from app.auth import get_current_user, require_user

router = APIRouter(prefix="/api/chat", tags=["答疑"])


class OptimizeRequest(BaseModel):
    text: str


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
    user = require_user(user) if user else {"user_id": 0}
    result = await chat_service.send_message(
        session_id=session_id,
        content=body.content,
        user_id=user.get("user_id", 0),
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

    user = require_user(user) if user else {"user_id": 0}
    result = await chat_service.send_message(
        session_id=session_id,
        content=content,
        image_data=image_data,
        user_id=user.get("user_id", 0),
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
