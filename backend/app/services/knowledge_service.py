"""知识图谱服务——知识点结构 + 个性化薄弱数据融合"""

import json
from pathlib import Path
from typing import Optional

from app.db.database import get_db


def _load_seed_graph() -> dict:
    """从 seed_data/knowledge_graph.json 加载基础图谱"""
    path = Path(__file__).parent.parent.parent / "seed_data" / "knowledge_graph.json"
    if not path.exists():
        return {"nodes": [], "edges": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def get_knowledge_graph(user_id: Optional[int] = None) -> dict:
    """获取知识图谱，可选融合用户薄弱点数据"""
    graph = _load_seed_graph()
    if not graph.get("nodes"):
        return graph

    # 从 parent 字段生成包含边
    node_ids = {n["id"] for n in graph["nodes"]}
    existing_edges = {(e["source"], e["target"]) for e in graph.get("edges", [])}
    for node in graph["nodes"]:
        parent = node.get("parent")
        if parent and parent in node_ids and (parent, node["id"]) not in existing_edges:
            graph["edges"].append({
                "source": parent,
                "target": node["id"],
                "type": "contains",
                "label": "包含",
            })

    # 融合用户的薄弱知识点（从 error_logs + analysis 分析）
    if user_id:
        mastery = await _calc_user_mastery(user_id)
        for node in graph["nodes"]:
            node["mastery"] = mastery.get(node["id"], None)

    return graph


async def _calc_user_mastery(user_id: int) -> dict:
    """计算用户对各知识点的掌握度 (0~1)"""
    db = await get_db()
    mastery = {}

    # 从 error_logs 统计：从题目关联知识点
    # 先用 learning_summaries 中的 subject 标签
    cursor = await db.execute(
        "SELECT subjects_json FROM learning_summaries "
        "WHERE session_id IN (SELECT session_id FROM sessions WHERE user_id = ?) "
        "ORDER BY updated_at DESC",
        (user_id,),
    )
    rows = await cursor.fetchall()
    await cursor.close()

    # 简单映射：学科名称 → 章节点
    subject_nodes = {
        "力学": "mechanics", "电学": "electromagnetism",
        "热学": "thermodynamics", "光学": "optics", "近代物理": "modern_physics",
    }
    for row in rows:
        subjects = json.loads(row["subjects_json"]) if row["subjects_json"] else []
        for subj in subjects:
            node_id = subject_nodes.get(subj)
            if node_id:
                mastery[node_id] = 0.5  # 标记为有过学习记录

    return mastery
