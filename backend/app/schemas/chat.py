"""多模态答疑模块的请求/响应模型"""

from pydantic import BaseModel, Field
from typing import Optional


class ChatSendRequest(BaseModel):
    """发送文字消息请求"""
    content: str = Field(..., min_length=1, description="用户输入的文字内容")


class ChatUploadRequest(BaseModel):
    """上传图片并提问请求"""
    content: str = Field("", description="用户输入的文字内容（可选）")
    # 图片以 multipart/form-data 上传，不由此模型定义


class ChatMessage(BaseModel):
    """单条聊天记录"""
    id: int
    role: str  # 'user' | 'assistant'
    content: str
    image_url: Optional[str] = None
    model_used: Optional[str] = None
    created_at: str


class ChatResponse(BaseModel):
    """AI 回答响应"""
    content: str
    model_used: str
    confidence: float
    history: list[ChatMessage]


class ChatHistoryResponse(BaseModel):
    """对话历史响应"""
    messages: list[ChatMessage]
    total: int
