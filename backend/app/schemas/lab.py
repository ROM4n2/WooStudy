"""虚拟实验室模块的请求/响应模型"""

from pydantic import BaseModel
from typing import Optional


class LabItem(BaseModel):
    """实验项"""
    id: str       # 实验标识（PhET 仿真 ID）
    name: str     # 实验名称
    description: str
    url: str      # PhET iframe 嵌入 URL
    category: str  # '力学' / '电学' / '光学' / '热学'


class LabListResponse(BaseModel):
    """可用实验列表"""
    labs: list[LabItem]


class LabSessionCreateRequest(BaseModel):
    """记录实验会话请求"""
    lab_name: str
    lab_title: str
    duration_seconds: int


class LabSessionResponse(BaseModel):
    """实验会话记录响应"""
    id: int
    lab_name: str
    lab_title: str
    started_at: str
    duration_seconds: Optional[int] = None
