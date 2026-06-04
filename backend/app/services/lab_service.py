"""虚拟实验室服务——实验列表 + 会话记录"""

from app.db.database import get_db

# PhET 仿真列表（可免费嵌入 iframe）
# 来源：https://phet.colorado.edu/en/simulations/filter?sort=alpha&view=grid
PHET_LABS = [
    {
        "id": "pendulum-lab",
        "name": "单摆实验",
        "description": "研究摆长、摆角和质量对摆动周期的影响",
        "url": "https://phet.colorado.edu/sims/html/pendulum-lab/latest/pendulum-lab_all.html",
        "category": "力学",
    },
    {
        "id": "forces-motion-basics",
        "name": "力和运动基础",
        "description": "探索力和质量如何影响物体的运动",
        "url": "https://phet.colorado.edu/sims/html/forces-and-motion-basics/latest/forces-and-motion-basics_all.html",
        "category": "力学",
    },
    {
        "id": "projectile-motion",
        "name": "平抛运动",
        "description": "研究初速度、角度和高度对抛体轨迹的影响",
        "url": "https://phet.colorado.edu/sims/html/projectile-motion/latest/projectile-motion_all.html",
        "category": "力学",
    },
    {
        "id": "circuit-construction-kit-dc",
        "name": "电路搭建（直流）",
        "description": "搭建串联和并联电路，测量电流和电压",
        "url": "https://phet.colorado.edu/sims/html/circuit-construction-kit-dc/latest/circuit-construction-kit-dc_all.html",
        "category": "电学",
    },
    {
        "id": "faradays-law",
        "name": "法拉第电磁感应",
        "description": "探究磁场变化如何产生感应电流",
        "url": "https://phet.colorado.edu/sims/html/faradays-law/latest/faradays-law_all.html",
        "category": "电学",
    },
    {
        "id": "bending-light",
        "name": "光的折射",
        "description": "探究光在不同介质中的折射和全反射",
        "url": "https://phet.colorado.edu/sims/html/bending-light/latest/bending-light_all.html",
        "category": "光学",
    },
    {
        "id": "wave-on-a-string",
        "name": "绳波实验",
        "description": "研究波的传播、反射和干涉",
        "url": "https://phet.colorado.edu/sims/html/wave-on-a-string/latest/wave-on-a-string_all.html",
        "category": "力学",
    },
    {
        "id": "energy-skate-park",
        "name": "能量滑板公园",
        "description": "探究动能和势能的转换与守恒",
        "url": "https://phet.colorado.edu/sims/html/energy-skate-park/latest/energy-skate-park_all.html",
        "category": "力学",
    },
]


async def get_lab_list() -> dict:
    """获取可用实验列表"""
    return {"labs": PHET_LABS}


async def record_session(
    session_id: str,
    lab_name: str,
    lab_title: str,
    duration_seconds: int,
) -> dict:
    """记录用户在某个实验上的会话时长"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id FROM lab_sessions WHERE session_id = ? AND lab_name = ? AND ended_at IS NULL ORDER BY started_at DESC LIMIT 1",
        (session_id, lab_name),
    )
    existing = await cursor.fetchone()
    await cursor.close()

    if existing:
        # 更新结束时间
        await db.execute(
            "UPDATE lab_sessions SET ended_at = datetime('now'), duration_seconds = ? WHERE id = ?",
            (duration_seconds, existing["id"]),
        )
    else:
        # 新建记录
        await db.execute(
            "INSERT INTO lab_sessions (session_id, lab_name, lab_title, duration_seconds) VALUES (?, ?, ?, ?)",
            (session_id, lab_name, lab_title, duration_seconds),
        )

    await db.commit()
    return {"success": True}
