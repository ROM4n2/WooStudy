"""虚拟实验室路由"""

from fastapi import APIRouter
from app.schemas.lab import LabSessionCreateRequest
from app.services import lab_service

router = APIRouter(prefix="/api/lab", tags=["实验室"])


@router.get("/list")
async def get_lab_list() -> dict:
    """获取可用实验列表"""
    return await lab_service.get_lab_list()


@router.post("/session")
async def record_session(
    session_id: str,
    body: LabSessionCreateRequest,
) -> dict:
    """记录实验会话"""
    return await lab_service.record_session(
        session_id=session_id,
        lab_name=body.lab_name,
        lab_title=body.lab_title,
        duration_seconds=body.duration_seconds,
    )
