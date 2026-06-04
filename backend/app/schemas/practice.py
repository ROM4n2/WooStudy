"""智能刷题模块的请求/响应模型"""

from pydantic import BaseModel, Field
from typing import Optional


class PracticeQuestion(BaseModel):
    """单道刷题"""
    id: int
    content: str
    question_type: str
    options: Optional[list[str]] = None
    subject: str
    difficulty: int


class PracticeListResponse(BaseModel):
    """刷题列表响应"""
    questions: list[PracticeQuestion]
    total: int


class SubmitAnswerRequest(BaseModel):
    """提交答案请求（session_id 来自 query，不在 body 中）"""
    question_id: int
    answer: str = Field(..., min_length=1, description="用户答案")


class SubmitAnswerResponse(BaseModel):
    """提交答案响应"""
    question_id: int
    is_correct: bool
    correct_answer: str
    explanation: Optional[str] = None
    error_log_id: Optional[int] = None  # 如果做错了，对应错题本记录 ID
