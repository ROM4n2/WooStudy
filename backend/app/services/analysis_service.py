"""学情分析服务——做题统计 + AI 深度分析"""

import json
from app.db.database import get_db, db_execute, db_fetch_all, db_fetch_one
from app.ai.dispatcher import dispatch_analyze
from app.services import get_user_api_keys


async def _ensure_session(session_id: str) -> None:
    """如果 session 不存在则创建"""
    db = await get_db()
    row = await db_fetch_one("SELECT id FROM sessions WHERE session_id = ?", (session_id,))
    if row is None:
        await db_execute("INSERT INTO sessions (session_id) VALUES (?)", (session_id,))
        await db.commit()


async def get_report(session_id: str, force_refresh: bool = False, user_id: int = 0) -> dict:
    """
    获取学情分析报告

    Strategy:
    - 先从缓存读取，如果 5 分钟内生成过且非强制刷新，直接返回
    - 否则从错题统计数据生成新的报告
    """
    db = await get_db()

    # 1. 检查缓存
    if not force_refresh:
        cached = await db_fetch_one(
            "SELECT report_json, generated_at FROM analysis_cache WHERE session_id = ?",
            (session_id,),
        )
        if cached:
            # 检查是否 5 分钟内生成的
            # todo: 更精确的时间判断
            return json.loads(cached["report_json"])

    # 2. 统计各科错题数据
    stats_rows = await db_fetch_all(
        """SELECT subject,
                  COUNT(*) as total,
                  SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_count
           FROM error_logs WHERE session_id = ?
           GROUP BY subject""",
        (session_id,),
    )

    # 总统计
    total_row = await db_fetch_one(
        """SELECT COUNT(*) as total,
                  SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_count
           FROM error_logs WHERE session_id = ?""",
        (session_id,),
    )

    total_questions = total_row["total"] or 0
    total_correct = total_row["correct_count"] or 0
    total_correct_rate = total_correct / total_questions if total_questions > 0 else 0

    # 3. 格式化统计信息，用于 AI 深度分析
    stats_text = f"学生做题总览：共 {total_questions} 题，正确率 {total_correct_rate:.1%}\n\n各科详情：\n"
    radar_data = []
    for row in stats_rows:
        rate = row["correct_count"] / row["total"] if row["total"] > 0 else 0
        stats_text += f"- {row['subject']}: {row['total']} 题，正确率 {rate:.1%}\n"
        radar_data.append({
            "subject": row["subject"],
            "correct_rate": round(rate, 2),
            "question_count": row["total"],
        })

    # 获取具体的错题信息
    wrong_rows = await db_fetch_all(
        """SELECT q.content, e.user_answer, q.correct_answer, e.wrong_reason, e.subject
           FROM error_logs e
           LEFT JOIN questions q ON e.question_id = q.id
           WHERE e.session_id = ? AND e.is_correct = 0
           LIMIT 10""",
        (session_id,),
    )

    if wrong_rows:
        stats_text += "\n典型错题示例：\n"
        for r in wrong_rows:
            stats_text += f"- [{r['subject']}] {r['content'][:50]}... 错答: {r['user_answer']} 正解: {r['correct_answer']}\n"

    # 4. 获取用户 API Key 并调用 AI 进行深度分析
    keys = await get_user_api_keys(user_id) if user_id else {"deepseek_key": ""}
    ai_result = await dispatch_analyze(stats_text, deepseek_key=keys["deepseek_key"])

    # 尝试解析 AI 返回的 JSON
    try:
        analysis = json.loads(ai_result["content"])
    except (json.JSONDecodeError, KeyError):
        # 返回自动统计（不依赖 AI）
        analysis = {
            "radar_data": radar_data,
            "weaknesses": [],
            "summary": "AI 深度分析暂不可用，以上为基础统计数据。",
        }

    # 5. 覆盖 AI 的雷达数据为实际统计（更准确）
    analysis["radar_data"] = radar_data

    report = {
        "session_id": session_id,
        "total_questions": total_questions,
        "total_correct_rate": round(total_correct_rate, 2),
        "radar_data": radar_data,
        "weaknesses": analysis.get("weaknesses", []),
        "summary": analysis.get("summary", "继续保持学习！"),
    }

    # 6. 写入缓存（确保 session 存在以符合外键约束）
    await _ensure_session(session_id)
    await db_execute(
        "INSERT OR REPLACE INTO analysis_cache (session_id, report_json, generated_at) VALUES (?, ?, datetime('now'))",
        (session_id, json.dumps(report, ensure_ascii=False)),
    )
    await db.commit()

    return report


async def get_learning_journey(session_id: str) -> dict:
    """获取学习历程数据（按天组织的学习摘要 + 知识点覆盖 + 活动明细 + 热力图）"""
    # 1. 学习摘要
    summary_rows = await db_fetch_all(
        """SELECT date, subjects_json, summary_text, updated_at
           FROM learning_summaries
           WHERE session_id = ?
           ORDER BY date DESC
           LIMIT 60""",
        (session_id,),
    )

    summary_map = {}
    all_subjects = set()
    for r in summary_rows:
        subjects = json.loads(r["subjects_json"]) if r["subjects_json"] else []
        all_subjects.update(subjects)
        summary_map[r["date"]] = {
            "subjects": subjects,
            "summary": (r["summary_text"] or "")[:200],
        }

    # 2. 聊天活动统计
    chat_rows = await db_fetch_all(
        """SELECT date(created_at) as day, COUNT(*) as count
           FROM chat_history
           WHERE session_id = ? AND role = 'user'
           GROUP BY day ORDER BY day DESC LIMIT 60""",
        (session_id,),
    )
    chat_map = {r["day"]: r["count"] for r in chat_rows}

    # 3. 刷题活动统计
    practice_rows = await db_fetch_all(
        """SELECT date(created_at) as day,
                  COUNT(*) as total,
                  SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
           FROM error_logs
           WHERE session_id = ?
           GROUP BY day ORDER BY day DESC LIMIT 60""",
        (session_id,),
    )
    practice_map = {r["day"]: {"total": r["total"], "correct": r["correct"]} for r in practice_rows}

    # 4. 错题复习统计
    review_rows = await db_fetch_all(
        """SELECT date(updated_at) as day, COUNT(*) as count
           FROM error_logs
           WHERE session_id = ? AND reviewed = 1
           GROUP BY day ORDER BY day DESC LIMIT 60""",
        (session_id,),
    )
    review_map = {r["day"]: r["count"] for r in review_rows}

    # 5. 实验室统计
    lab_rows = await db_fetch_all(
        """SELECT date(started_at) as day, COUNT(*) as count
           FROM lab_sessions
           WHERE session_id = ?
           GROUP BY day ORDER BY day DESC LIMIT 60""",
        (session_id,),
    )
    lab_map = {r["day"]: r["count"] for r in lab_rows}

    # 6. 合并每日数据
    all_dates = set()
    all_dates.update(summary_map.keys())
    all_dates.update(chat_map.keys())
    all_dates.update(practice_map.keys())
    all_dates.update(review_map.keys())
    all_dates.update(lab_map.keys())

    days = []
    heatmap = {}

    for date_str in sorted(all_dates, reverse=True):
        summary = summary_map.get(date_str, {})
        subjects = summary.get("subjects", [])
        all_subjects.update(subjects)

        chat_count = chat_map.get(date_str, 0)
        practice = practice_map.get(date_str, {"total": 0, "correct": 0})
        review_count = review_map.get(date_str, 0)
        lab_count = lab_map.get(date_str, 0)

        # 计算学习强度 (0~1)
        activities_count = chat_count + practice["total"] + review_count + lab_count
        intensity = min(activities_count / 15, 1.0)  # 一天15个活动算满

        # 热力图数据
        ym = date_str[:7]  # "2026-06"
        day_num = str(int(date_str[8:10]))  # "4"
        if ym not in heatmap:
            heatmap[ym] = {}
        heatmap[ym][day_num] = round(intensity, 2)

        activities = []
        if chat_count > 0:
            activities.append({"type": "chat", "label": "答疑", "count": chat_count})
        if practice["total"] > 0:
            rate = round(practice["correct"] / practice["total"] * 100) if practice["total"] > 0 else 0
            activities.append({
                "type": "practice", "label": "刷题",
                "count": practice["total"], "correct": practice["correct"], "rate": rate,
            })
        if review_count > 0:
            activities.append({"type": "review", "label": "复习", "count": review_count})
        if lab_count > 0:
            activities.append({"type": "lab", "label": "实验", "count": lab_count})

        days.append({
            "date": date_str,
            "subjects": subjects,
            "summary": summary.get("summary", ""),
            "activities": activities,
            "intensity": intensity,
        })

    # 学习连续天数
    streak = _calc_streak([d["date"] for d in days])

    return {
        "days": days,
        "total_days": len(days),
        "streak": streak,
        "subjects_covered": sorted(all_subjects),
        "heatmap": heatmap,
    }


def _calc_streak(dates: list[str]) -> int:
    """计算连续学习天数"""
    from datetime import datetime, timedelta
    if not dates:
        return 0
    sorted_dates = sorted(set(dates), reverse=True)
    streak = 1
    for i in range(len(sorted_dates) - 1):
        d1 = datetime.strptime(sorted_dates[i], "%Y-%m-%d")
        d2 = datetime.strptime(sorted_dates[i + 1], "%Y-%m-%d")
        if (d1 - d2).days == 1:
            streak += 1
        else:
            break
    return streak
