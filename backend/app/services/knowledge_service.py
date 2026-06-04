"""知识图谱服务——DB 持久化存储 + CRUD + 用户标记 + 学情融合"""

import json
from typing import Optional

from app.db.database import get_db, db_execute, db_fetch_all, db_fetch_one


# ── 读取图谱 ──


async def get_knowledge_graph(user_id: Optional[int] = None) -> dict:
    """从 DB 获取完整知识图谱（仅 approved 节点），融合用户标记和掌握度"""
    nodes = [dict(row) for row in await db_fetch_all(
        "SELECT id, label, category, subject, parent_id, description, importance, source "
        "FROM knowledge_nodes WHERE status = 'approved' ORDER BY subject, category"
    )]
    # 统一字段名
    for n in nodes:
        n["parent"] = n.pop("parent_id")

    edges = [dict(row) for row in await db_fetch_all(
        "SELECT source_id, target_id, type, label FROM knowledge_edges"
    )]
    # 统一字段名
    for e in edges:
        e["source"] = e.pop("source_id")
        e["target"] = e.pop("target_id")

    if not nodes:
        return {"nodes": [], "edges": []}

    # 融合用户掌握度
    if user_id:
        mastery = await _calc_user_mastery(user_id)
        markers = await _get_user_markers(user_id)
        marker_map = {}
        for m in markers:
            nid = m["node_id"]
            if nid not in marker_map:
                marker_map[nid] = []
            marker_map[nid].append(m["marker_type"])

        for n in nodes:
            n["mastery"] = mastery.get(n["id"], None)
            n["markers"] = marker_map.get(n["id"], [])

    return {"nodes": nodes, "edges": edges}


# ── 掌握度计算（含学情 + 标记加权） ──


async def _calc_user_mastery(user_id: int) -> dict:
    """计算用户对各知识点的掌握度 (0~1)，结合学习记录和标记"""
    mastery = {}

    subject_nodes = {
        "力学": "mechanics", "电学": "electromagnetism",
        "热学": "thermodynamics", "光学": "optics", "近代物理": "modern_physics",
    }

    # 1. 学习摘要中的学科 → 对应章节点
    rows = await db_fetch_all(
        "SELECT subjects_json FROM learning_summaries "
        "WHERE session_id IN (SELECT session_id FROM sessions WHERE user_id = ?) "
        "ORDER BY updated_at DESC",
        (user_id,),
    )
    for row in rows:
        subjects = json.loads(row["subjects_json"]) if row["subjects_json"] else []
        for subj in subjects:
            nid = subject_nodes.get(subj)
            if nid:
                mastery[nid] = max(mastery.get(nid, 0), 0.5)

    # 2. 错题本 → 低掌握度
    rows2 = await db_fetch_all(
        "SELECT subject, COUNT(*) as cnt FROM error_logs "
        "WHERE session_id IN (SELECT session_id FROM sessions WHERE user_id = ?) "
        "AND is_correct = 0 GROUP BY subject",
        (user_id,),
    )
    for row in rows2:
        nid = subject_nodes.get(row["subject"])
        if nid:
            # 错题越多掌握度越低
            base = mastery.get(nid, 0.5)
            mastery[nid] = max(0.1, base - row["cnt"] * 0.05)

    # 3. 用户标记影响
    rows3 = await db_fetch_all(
        "SELECT node_id, marker_type FROM knowledge_markers WHERE user_id = ?",
        (user_id,),
    )
    for row in rows3:
        nid = row["node_id"]
        mt = row["marker_type"]
        if mt == "weak":
            mastery[nid] = min(mastery.get(nid, 0.5), 0.3)
        elif mt == "important":
            mastery[nid] = max(mastery.get(nid, 0.5), 0.6)

    return mastery


# ── 用户标记 ──


async def _get_user_markers(user_id: int) -> list:
    """获取用户所有标记"""
    db = await get_db()
    rows = await db_fetch_all(
        "SELECT node_id, marker_type FROM knowledge_markers WHERE user_id = ?",
        (user_id,),
    )
    return [dict(r) for r in rows]


async def add_marker(user_id: int, node_id: str, marker_type: str, note: str = "") -> dict:
    """添加标记"""
    db = await get_db()
    await db_execute(
        "INSERT OR REPLACE INTO knowledge_markers (user_id, node_id, marker_type, note) VALUES (?, ?, ?, ?)",
        (user_id, node_id, marker_type, note),
    )
    await db.commit()
    return {"ok": True}


async def remove_marker(user_id: int, node_id: str, marker_type: str) -> bool:
    """取消标记"""
    db = await get_db()
    cursor = await db.execute(
        "DELETE FROM knowledge_markers WHERE user_id = ? AND node_id = ? AND marker_type = ?",
        (user_id, node_id, marker_type),
    )
    rowcount = cursor.rowcount
    await db.commit()
    await cursor.close()
    return rowcount > 0


async def get_user_markers(user_id: int) -> list:
    """获取用户所有标记"""
    rows = await db_fetch_all(
        "SELECT km.id, km.node_id, km.marker_type, km.note, kn.label "
        "FROM knowledge_markers km "
        "LEFT JOIN knowledge_nodes kn ON kn.id = km.node_id "
        "WHERE km.user_id = ? ORDER BY km.created_at DESC",
        (user_id,),
    )
    return [dict(r) for r in rows]


# ── 管理员 CRUD ──


async def check_admin_role(user_id: int) -> bool:
    """检查用户是否为管理员"""
    row = await db_fetch_one("SELECT role FROM users WHERE id = ?", (user_id,))
    return row is not None and row["role"] == "admin"


async def create_node(user_id: int, data: dict) -> dict:
    """创建知识点节点"""
    db = await get_db()
    await db_execute(
        """INSERT INTO knowledge_nodes (id, label, category, subject, parent_id, description, importance, source, created_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'user', ?)""",
        (data["id"], data["label"], data["category"], data["subject"],
         data.get("parent_id"), data.get("description", ""), data.get("importance", 3), user_id),
    )
    await db.commit()
    return {"id": data["id"], "ok": True}


async def update_node(node_id: str, data: dict) -> bool:
    """更新知识点节点"""
    db = await get_db()
    fields = []
    params = []
    for key in ("label", "category", "subject", "parent_id", "description", "importance"):
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if not fields:
        return True
    fields.append("updated_at = datetime('now')")
    params.append(node_id)
    db = await get_db()
    cursor = await db.execute(
        f"UPDATE knowledge_nodes SET {', '.join(fields)} WHERE id = ?", params
    )
    rowcount = cursor.rowcount
    await db.commit()
    await cursor.close()
    return rowcount > 0


async def delete_node(node_id: str) -> bool:
    """删除知识点节点（级联删除关联边和标记）"""
    db = await get_db()
    await db_execute("DELETE FROM knowledge_markers WHERE node_id = ?", (node_id,))
    await db_execute("DELETE FROM knowledge_edges WHERE source_id = ? OR target_id = ?", (node_id, node_id))
    db = await get_db()
    cursor = await db.execute("DELETE FROM knowledge_nodes WHERE id = ?", (node_id,))
    rowcount = cursor.rowcount
    await db.commit()
    await cursor.close()
    return rowcount > 0


async def create_edge(user_id: int, data: dict) -> dict:
    """创建关联边"""
    db = await get_db()
    await db_execute(
        "INSERT OR IGNORE INTO knowledge_edges (source_id, target_id, type, label, created_by) VALUES (?, ?, ?, ?, ?)",
        (data["source_id"], data["target_id"], data.get("type", "related"), data.get("label", ""), user_id),
    )
    await db.commit()
    return {"ok": True}


async def delete_edge(source_id: str, target_id: str, edge_type: str) -> bool:
    """删除关联边"""
    db = await get_db()
    cursor = await db.execute(
        "DELETE FROM knowledge_edges WHERE source_id = ? AND target_id = ? AND type = ?",
        (source_id, target_id, edge_type),
    )
    rowcount = cursor.rowcount
    await db.commit()
    await cursor.close()
    return rowcount > 0


# ── 用户贡献 ──


async def submit_contribution(user_id: int, data: dict) -> dict:
    """用户提交知识点贡献（自动生成 ID，状态为 pending）"""
    import uuid
    node_id = data.get("id") or f"contrib_{uuid.uuid4().hex[:8]}"
    db = await get_db()
    await db_execute(
        """INSERT INTO knowledge_nodes
           (id, label, category, subject, parent_id, description, importance, source, created_by, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'user', ?, 'pending')""",
        (node_id, data["label"], data.get("category", "topic"), data["subject"],
         data.get("parent_id"), data.get("description", ""), data.get("importance", 3), user_id),
    )
    await db.commit()
    return {"id": node_id, "status": "pending", "ok": True}


async def get_pending_contributions() -> list:
    """管理员：获取所有待审核的知识点"""
    rows = await db_fetch_all(
        """SELECT id, label, category, subject, parent_id, description, importance,
                  created_by, created_at
           FROM knowledge_nodes WHERE status = 'pending'
           ORDER BY created_at DESC"""
    )
    return [dict(r) for r in rows]


async def approve_contribution(node_id: str) -> bool:
    """管理员：批准知识点"""
    db = await get_db()
    cursor = await db.execute(
        "UPDATE knowledge_nodes SET status = 'approved', updated_at = datetime('now') WHERE id = ? AND status = 'pending'",
        (node_id,),
    )
    rowcount = cursor.rowcount
    await db.commit()
    await cursor.close()
    return rowcount > 0


async def reject_contribution(node_id: str) -> bool:
    """管理员：拒绝知识点（不移除，保留供查看）"""
    db = await get_db()
    cursor = await db.execute(
        "UPDATE knowledge_nodes SET status = 'rejected', updated_at = datetime('now') WHERE id = ? AND status = 'pending'",
        (node_id,),
    )
    rowcount = cursor.rowcount
    await db.commit()
    await cursor.close()
    return rowcount > 0
