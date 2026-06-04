"""学情分析路由"""

from fastapi import APIRouter, Depends
from app.services import analysis_service
from app.auth import get_current_user, require_user

router = APIRouter(prefix="/api/analysis", tags=["学情分析"])


@router.get("/report")
async def get_report(
    session_id: str,
    force_refresh: bool = False,
    user: dict = Depends(get_current_user),
) -> dict:
    """获取学情分析报告"""
    user = require_user(user) if user else {"user_id": 0}
    return await analysis_service.get_report(
        session_id=session_id,
        force_refresh=force_refresh,
        user_id=user.get("user_id", 0),
    )


@router.get("/journey")
async def get_journey(session_id: str) -> dict:
    """获取学习历程"""
    return await analysis_service.get_learning_journey(session_id)
