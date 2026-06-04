"""智能刷题路由"""

from fastapi import APIRouter, HTTPException
from app.schemas.practice import SubmitAnswerRequest
from app.services import practice_service

router = APIRouter(prefix="/api/practice", tags=["刷题"])


@router.get("")
async def get_questions(
    session_id: str,
    subject: str | None = None,
    difficulty: int | None = None,
    count: int = 5,
) -> dict:
    """获取推荐题目"""
    return await practice_service.get_practice_questions(
        session_id=session_id,
        subject=subject,
        difficulty=difficulty,
        count=min(count, 20),  # 一次最多 20 题
    )


@router.post("/submit")
async def submit_answer(session_id: str, body: SubmitAnswerRequest) -> dict:
    """提交答案（session_id 来自 query 参数，由 axios 拦截器自动注入）"""
    try:
        return await practice_service.submit_answer(
            session_id=session_id,
            question_id=body.question_id,
            answer=body.answer,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
