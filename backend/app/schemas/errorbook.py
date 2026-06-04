"""错题本模块的请求/响应模型"""

from pydantic import BaseModel
from typing import Optional


class ErrorLogItem(BaseModel):
    """单条错题记录"""
    id: int
    question_id: Optional[int] = None
    content: str  # 题目内容
    user_answer: str
    correct_answer: str
    explanation: Optional[str] = None
    wrong_reason: Optional[str] = None
    subject: Optional[str] = None
    reviewed: bool
    created_at: str
    variants: list["VariantItem"] = []  # 关联的变式题


class ErrorLogListResponse(BaseModel):
    """错题列表响应（支持按科目分组）"""
    total: int
    items: list[ErrorLogItem]


class ErrorLogGroupedResponse(BaseModel):
    """按科目分组的错题响应"""
    groups: dict[str, list[ErrorLogItem]]  # 如 {"力学": [...], "电学": [...]}
    total: int


class ReviewRequest(BaseModel):
    """标记已复习请求"""
    reviewed: bool = True


class VariantItem(BaseModel):
    """变式题记录"""
    id: int
    content: str
    options: Optional[list[str]] = None
    correct_answer: str
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    created_at: str


class VariantGenerateResponse(BaseModel):
    """变式题生成响应"""
    error_log_id: int
    variant: VariantItem
