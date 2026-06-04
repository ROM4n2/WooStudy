"""智能刷题服务——题目获取 + 答案提交 + 错题入库"""

from app.db.database import get_db, db_execute, db_fetch_all, db_fetch_one


async def get_practice_questions(
    session_id: str,
    subject: str | None = None,
    difficulty: int | None = None,
    count: int = 5,
) -> dict:
    """
    获取刷题列表

    选题策略：
    1. 优先推荐用户错题对应的知识点（薄弱点巩固）
    2. 排除最近已做过的题
    3. 随机排序，提升多样性
    4. 如果指定了 subject 和 difficulty，按条件筛选
    """
    # 获取用户已做过的题目 ID
    done_rows = await db_fetch_all(
        "SELECT DISTINCT question_id FROM error_logs WHERE session_id = ?",
        (session_id,),
    )
    done_ids = [row["question_id"] for row in done_rows]

    # 获取用户薄弱科目（错题最多的科目）
    weak_rows = await db_fetch_all(
        """SELECT subject FROM error_logs
           WHERE session_id = ? AND is_correct = 0
           GROUP BY subject ORDER BY COUNT(*) DESC LIMIT 3""",
        (session_id,),
    )
    weak_subjects = [row["subject"] for row in weak_rows]

    # 构建查询
    query = "SELECT id, content, question_type, options_json, subject, difficulty, correct_answer, explanation FROM questions"
    conditions = []
    params = []

    if done_ids:
        placeholders = ",".join(["?"] * len(done_ids))
        conditions.append(f"id NOT IN ({placeholders})")
        params.extend(done_ids)

    if subject:
        conditions.append("subject = ?")
        params.append(subject)

    if difficulty:
        conditions.append("difficulty = ?")
        params.append(difficulty)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # 优先推荐薄弱科目
    if weak_subjects and not subject:
        order_clause = "ORDER BY CASE WHEN subject IN ({}) THEN 0 ELSE 1 END, RANDOM()".format(
            ",".join(["?"] * len(weak_subjects))
        )
        query += " " + order_clause
        params.extend(weak_subjects)
    else:
        query += " ORDER BY RANDOM()"

    query += " LIMIT ?"
    params.append(count)

    rows = await db_fetch_all(query, params)

    import json
    questions = [
        {
            "id": row["id"],
            "content": row["content"],
            "question_type": row["question_type"],
            "options": json.loads(row["options_json"]) if row["options_json"] else None,
            "subject": row["subject"],
            "difficulty": row["difficulty"],
        }
        for row in rows
    ]

    return {
        "questions": questions,
        "total": len(questions),
        "weak_subjects": weak_subjects,  # 前端可据此展示"薄弱科目推荐"
    }


async def submit_answer(
    session_id: str,
    question_id: int,
    answer: str,
) -> dict:
    """
    提交答案：判断对错 → 记录到错题本 → 返回结果
    """
    # 确保 session 存在（满足外键约束）
    row_s = await db_fetch_one("SELECT id FROM sessions WHERE session_id = ?", (session_id,))
    if row_s is None:
        await db_execute("INSERT INTO sessions (session_id) VALUES (?)", (session_id,))
        await db.commit()

    # 获取正确答案
    row = await db_fetch_one(
        "SELECT correct_answer, explanation, subject FROM questions WHERE id = ?",
        (question_id,),
    )

    if row is None:
        raise ValueError(f"题目不存在: {question_id}")

    correct_answer = row["correct_answer"]
    is_correct = (answer.strip().upper() == correct_answer.strip().upper())

    error_log_id = None

    if not is_correct:  # 只记录错题到错题本
        await db_execute(
            """INSERT INTO error_logs (session_id, question_id, user_answer, is_correct, subject)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, question_id, answer, 0, row["subject"]),
        )
        await db.commit()

        result = await db_fetch_one("SELECT last_insert_rowid()")
        error_log_id = result[0] if result else None

    return {
        "question_id": question_id,
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "explanation": row["explanation"],
        "error_log_id": error_log_id,
    }
