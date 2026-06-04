"""错题本服务——错题 CRUD、变式出题"""

import json
from typing import Optional

from app.db.database import get_db, db_execute, db_fetch_all, db_fetch_one
from app.ai.dispatcher import dispatch_generate_variant
from app.services import get_user_api_keys


async def get_error_logs(
    session_id: str,
    subject: Optional[str] = None,
    reviewed: Optional[bool] = None,
    group_by_subject: bool = False,
) -> dict:
    """
    获取错题列表

    Args:
        session_id: 会话 ID
        subject: 按科目筛选（可选）
        reviewed: 按复习状态筛选（可选）
        group_by_subject: 是否按科目分组

    Returns:
        分组或未分组的错题列表
    """
    db = await get_db()
    conditions = ["e.session_id = ?"]
    params = [session_id]

    if subject:
        conditions.append("e.subject = ?")
        params.append(subject)
    if reviewed is not None:
        conditions.append("e.reviewed = ?")
        params.append(1 if reviewed else 0)

    query = f"""
        SELECT e.id, e.question_id, e.user_answer, e.is_correct, e.wrong_reason,
               e.subject, e.reviewed, e.created_at,
               q.content, q.correct_answer, q.explanation, q.options_json
        FROM error_logs e
        LEFT JOIN questions q ON e.question_id = q.id
        WHERE {' AND '.join(conditions)}
        ORDER BY e.created_at DESC
    """

    rows = await db_fetch_all(query, params)

    items = []
    for row in rows:
        # 获取关联的变式题
        variants = await _get_variants(db, row["id"])
        items.append(_row_to_error_item(row, variants))

    if group_by_subject:
        groups: dict[str, list] = {}
        for item in items:
            subj = item["subject"] or "未分类"
            groups.setdefault(subj, []).append(item)
        return {"groups": groups, "total": len(items)}

    return {"items": items, "total": len(items)}


async def mark_reviewed(error_log_id: int, reviewed: bool = True) -> dict:
    """标记错题为已复习/未复习"""
    db = await get_db()
    await db_execute(
        "UPDATE error_logs SET reviewed = ? WHERE id = ?",
        (1 if reviewed else 0, error_log_id),
    )
    await db.commit()
    return {"success": True}


async def generate_variant(error_log_id: int, session_id: str, user_id: int = 0) -> dict:
    """
    基于错题生成变式题

    1. 查出错题信息
    2. 调用 AI 生成变式
    3. 保存变式记录
    """
    # 1. 获取错题
    row = await db_fetch_one(
        """SELECT e.id, e.user_answer, e.wrong_reason, e.question_id,
                  q.content, q.correct_answer, q.options_json, q.explanation
           FROM error_logs e
           LEFT JOIN questions q ON e.question_id = q.id
           WHERE e.id = ?""",
        (error_log_id,),
    )

    if row is None:
        raise ValueError(f"错题记录不存在: {error_log_id}")

    # 2. 获取用户 API Key 并调用 AI
    keys = await get_user_api_keys(user_id) if user_id else {"deepseek_key": ""}
    ai_result = await dispatch_generate_variant(
        original_content=row["content"] or "(题目内容)",
        user_answer=row["user_answer"],
        correct_answer=row["correct_answer"],
        wrong_reason=row["wrong_reason"] or "未分析",
        deepseek_key=keys["deepseek_key"],
    )

    # 尝试解析返回的 JSON
    variant_data = _parse_variant_json(ai_result["content"])

    # 3. 保存变式
    db = await get_db()
    insert_cursor = await db.execute(
        """INSERT INTO variant_questions
           (error_log_id, content, options_json, correct_answer, generated_by)
           VALUES (?, ?, ?, ?, ?)""",
        (
            error_log_id,
            variant_data.get("content", ai_result["content"]),
            json.dumps(variant_data.get("options", []), ensure_ascii=False),
            variant_data.get("correct_answer", ""),
            ai_result.get("model", "deepseek"),
        ),
    )
    new_id = insert_cursor.lastrowid
    await db.commit()
    await insert_cursor.close()

    # 4. 返回
    return {
        "error_log_id": error_log_id,
        "variant": {
            "id": new_id,
            "content": variant_data.get("content", ai_result["content"]),
            "options": variant_data.get("options"),
            "correct_answer": variant_data.get("correct_answer", ""),
            "created_at": "",  # 由下一次查询补充
        },
    }


async def _get_variants(db, error_log_id: int) -> list[dict]:
    """获取错题关联的变式记录"""
    rows = await db_fetch_all(
        "SELECT id, content, options_json, correct_answer, user_answer, is_correct, created_at "
        "FROM variant_questions WHERE error_log_id = ? ORDER BY id",
        (error_log_id,),
    )
    return [
        {
            "id": r["id"],
            "content": r["content"],
            "options": json.loads(r["options_json"]) if r["options_json"] else None,
            "correct_answer": r["correct_answer"],
            "user_answer": r["user_answer"],
            "is_correct": r["is_correct"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def _row_to_error_item(row, variants: list) -> dict:
    return {
        "id": row["id"],
        "question_id": row["question_id"],
        "content": row["content"] or "(题目内容已删除)",
        "user_answer": row["user_answer"],
        "correct_answer": row["correct_answer"] or "",
        "explanation": row["explanation"],
        "wrong_reason": row["wrong_reason"],
        "subject": row["subject"],
        "reviewed": bool(row["reviewed"]),
        "created_at": row["created_at"],
        "variants": variants,
    }


def _parse_variant_json(text: str) -> dict:
    """
    从 AI 返回文本中提取 JSON 变式数据
    兼容：纯 JSON / 被 ```json ``` 包裹 / 前面有多余文字
    """
    import re
    # 尝试提取 ```json ... ``` 块
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        text = match.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 尝试在文本中寻找 {...}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    # 解析失败，返回原始文本
    return {"content": text, "options": [], "correct_answer": ""}
