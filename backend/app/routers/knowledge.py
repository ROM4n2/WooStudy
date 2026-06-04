"""知识图谱路由"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.services import knowledge_service
from app.auth import get_current_user

router = APIRouter(prefix="/api/knowledge", tags=["知识图谱"])


@router.get("/graph")
async def get_graph(user: dict = Depends(get_current_user)) -> dict:
    """获取完整知识图谱（含用户薄弱数据，如果已登录）"""
    uid = user.get("user_id") if user else None
    result = await knowledge_service.get_knowledge_graph(user_id=uid)
    return JSONResponse(result)
