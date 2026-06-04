"""学情分析路由"""

from fastapi import APIRouter
from app.services import analysis_service

router = APIRouter(prefix="/api/analysis", tags=["学情分析"])


@router.get("/report")
async def get_report(
    session_id: str,
    force_refresh: bool = False,
) -> dict:
    """获取学情分析报告"""
    return await analysis_service.get_report(
        session_id=session_id,
        force_refresh=force_refresh,
    )


@router.get("/journey")
async def get_journey(session_id: str) -> dict:
    """获取学习历程"""
    return await analysis_service.get_learning_journey(session_id)
