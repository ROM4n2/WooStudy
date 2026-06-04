"""错题本路由"""

from fastapi import APIRouter, Depends, HTTPException
from app.schemas.errorbook import ReviewRequest
from app.services import errorbook_service
from app.auth import get_current_user, require_user

router = APIRouter(prefix="/api/errorbook", tags=["错题本"])


@router.get("")
async def list_errors(
    session_id: str,
    subject: str | None = None,
    reviewed: bool | None = None,
    group_by_subject: bool = False,
) -> dict:
    """获取错题列表"""
    return await errorbook_service.get_error_logs(
        session_id=session_id,
        subject=subject,
        reviewed=reviewed,
        group_by_subject=group_by_subject,
    )


@router.put("/{error_id}/review")
async def mark_reviewed(error_id: int, body: ReviewRequest) -> dict:
    """标记已复习/未复习"""
    return await errorbook_service.mark_reviewed(error_id, body.reviewed)


@router.post("/{error_id}/variant")
async def generate_variant(
    error_id: int,
    session_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """生成变式题"""
    user = require_user(user)
    try:
        return await errorbook_service.generate_variant(
            error_id, session_id, user_id=user["user_id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
