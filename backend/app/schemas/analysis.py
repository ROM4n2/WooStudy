"""学情分析模块的请求/响应模型"""

from pydantic import BaseModel
from typing import Optional


class SubjectRadar(BaseModel):
    """单科雷达图数据点"""
    subject: str        # '力学' / '电学' / '热学' / '光学' / '近代物理'
    correct_rate: float  # 正确率 0~1
    question_count: int  # 该科总做题数


class WeaknessItem(BaseModel):
    """薄弱知识点"""
    subject: str
    concept: str
    suggestion: str      # 学习建议


class AnalysisReportResponse(BaseModel):
    """学情分析报告"""
    session_id: str
    total_questions: int
    total_correct_rate: float
    radar_data: list[SubjectRadar]
    weaknesses: list[WeaknessItem]
    summary: str          # 总体建议文字
    generated_at: str
