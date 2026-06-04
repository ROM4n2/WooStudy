"""知识图谱路由——读取 + 标记 + 管理员 CRUD"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.services import knowledge_service
from app.auth import get_current_user, require_user

router = APIRouter(prefix="/api/knowledge", tags=["知识图谱"])


# ── 公共：获取图谱 ──


@router.get("/graph")
async def get_graph(user: dict = Depends(get_current_user)) -> dict:
    """获取完整知识图谱（含用户标记和掌握度，如果已登录）"""
    uid = user.get("user_id") if user else None
    result = await knowledge_service.get_knowledge_graph(user_id=uid)
    return JSONResponse(result)


# ── 用户标记 ──


class MarkerRequest(BaseModel):
    node_id: str
    marker_type: str  # bookmark | weak | important
    note: str = ""


@router.post("/markers")
async def add_marker(body: MarkerRequest, user: dict = Depends(get_current_user)):
    """添加知识点标记"""
    u = require_user(user)
    if body.marker_type not in ("bookmark", "weak", "important"):
        raise HTTPException(400, "标记类型必须是 bookmark/weak/important")
    result = await knowledge_service.add_marker(u["user_id"], body.node_id, body.marker_type, body.note)
    return JSONResponse(result)


@router.delete("/markers")
async def remove_marker(
    node_id: str,
    marker_type: str,
    user: dict = Depends(get_current_user),
):
    """取消标记"""
    u = require_user(user)
    ok = await knowledge_service.remove_marker(u["user_id"], node_id, marker_type)
    if not ok:
        raise HTTPException(404, "标记不存在")
    return JSONResponse({"ok": True})


@router.get("/markers")
async def list_markers(user: dict = Depends(get_current_user)):
    """获取当前用户所有标记"""
    u = require_user(user)
    markers = await knowledge_service.get_user_markers(u["user_id"])
    return JSONResponse({"markers": markers})


# ── 管理员：节点 CRUD ──


async def _require_admin(user: dict = Depends(get_current_user)):
    """依赖注入：必须管理员"""
    u = require_user(user)
    is_admin = await knowledge_service.check_admin_role(u["user_id"])
    if not is_admin:
        raise HTTPException(403, "仅管理员可执行此操作")
    return u


class CreateNodeRequest(BaseModel):
    id: str
    label: str
    category: str  # chapter / section / topic
    subject: str
    parent_id: Optional[str] = None
    description: str = ""
    importance: int = 3


class UpdateNodeRequest(BaseModel):
    label: Optional[str] = None
    category: Optional[str] = None
    subject: Optional[str] = None
    parent_id: Optional[str] = None
    description: Optional[str] = None
    importance: Optional[int] = None


@router.post("/nodes")
async def create_node(body: CreateNodeRequest, admin: dict = Depends(_require_admin)):
    """创建知识点节点（管理员）"""
    if body.category not in ("chapter", "section", "topic"):
        raise HTTPException(400, "category 必须是 chapter/section/topic")
    result = await knowledge_service.create_node(admin["user_id"], body.model_dump())
    return JSONResponse(result)


@router.put("/nodes/{node_id}")
async def update_node(node_id: str, body: UpdateNodeRequest, admin: dict = Depends(_require_admin)):
    """更新知识点节点（管理员）"""
    ok = await knowledge_service.update_node(node_id, body.model_dump(exclude_none=True))
    if not ok:
        raise HTTPException(404, "节点不存在")
    return JSONResponse({"ok": True})


@router.delete("/nodes/{node_id}")
async def delete_node(node_id: str, admin: dict = Depends(_require_admin)):
    """删除知识点节点（管理员）"""
    ok = await knowledge_service.delete_node(node_id)
    if not ok:
        raise HTTPException(404, "节点不存在")
    return JSONResponse({"ok": True})


# ── 管理员：关联边 CRUD ──


class CreateEdgeRequest(BaseModel):
    source_id: str
    target_id: str
    type: str = "related"   # contains / prerequisite / related
    label: str = ""


@router.post("/edges")
async def create_edge(body: CreateEdgeRequest, admin: dict = Depends(_require_admin)):
    """创建关联边（管理员）"""
    if body.type not in ("contains", "prerequisite", "related"):
        raise HTTPException(400, "type 必须是 contains/prerequisite/related")
    result = await knowledge_service.create_edge(admin["user_id"], body.model_dump())
    return JSONResponse(result)


# ── 用户贡献 ──


class ContributionRequest(BaseModel):
    label: str
    subject: str
    category: str = "topic"
    parent_id: Optional[str] = None
    description: str = ""
    importance: int = 3


@router.post("/contributions")
async def submit_contribution(body: ContributionRequest, user: dict = Depends(get_current_user)):
    """提交知识点贡献（需登录，自动 pending）"""
    u = require_user(user)
    if body.subject not in ("力学", "电学", "热学", "光学", "近代物理"):
        raise HTTPException(400, "科目必须是：力学/电学/热学/光学/近代物理")
    if body.category not in ("chapter", "section", "topic"):
        raise HTTPException(400, "category 必须是 chapter/section/topic")
    result = await knowledge_service.submit_contribution(u["user_id"], body.model_dump())
    return JSONResponse(result)


@router.get("/pending")
async def list_pending(admin: dict = Depends(_require_admin)):
    """管理员：查看待审核贡献"""
    items = await knowledge_service.get_pending_contributions()
    return JSONResponse({"items": items})


@router.put("/pending/{node_id}/approve")
async def approve_contribution(node_id: str, admin: dict = Depends(_require_admin)):
    """管理员：批准知识点"""
    ok = await knowledge_service.approve_contribution(node_id)
    if not ok:
        raise HTTPException(404, "待审核节点不存在或已被处理")
    return JSONResponse({"ok": True})


@router.put("/pending/{node_id}/reject")
async def reject_contribution(node_id: str, admin: dict = Depends(_require_admin)):
    """管理员：拒绝知识点"""
    ok = await knowledge_service.reject_contribution(node_id)
    if not ok:
        raise HTTPException(404, "待审核节点不存在或已被处理")
    return JSONResponse({"ok": True})


@router.delete("/edges")
async def delete_edge(
    source_id: str,
    target_id: str,
    type: str = "related",
    admin: dict = Depends(_require_admin),
):
    """删除关联边（管理员）"""
    ok = await knowledge_service.delete_edge(source_id, target_id, type)
    if not ok:
        raise HTTPException(404, "边不存在")
    return JSONResponse({"ok": True})
