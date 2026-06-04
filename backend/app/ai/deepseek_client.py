"""DeepSeek V4 Pro API 封装——负责深度答疑、变式出题、学情分析（L2 层）"""

import httpx
from typing import Optional

from app.config import get_settings


# ---------- 系统提示词模板 ----------

PHYSICS_TUTOR_SYSTEM = """你是一名高中物理 AI 导师。请遵循以下原则：
1. 用 Socratic 式提问引导思考，而不是直接给答案
2. 涉及公式时，用 LaTeX $$...$$ 或 $...$ 格式
3. 复杂问题要分步骤推理，每步都解释物理原理
4. 结合生活实例帮助理解抽象概念
5. 回答末尾可以提一个追问来检验理解
6. 【非物理问题处理】如果用户提问与物理学习完全无关（如闲聊、娱乐、时事等），
   不要直接回答该问题。请转而关心用户是否学习累了需要休息，给予鼓励和加油。
   例如："看起来你有点累了？要不要休息一会儿？学物理需要保持好状态哦！"
   保持温暖、支持的语调。

当前角色：深度物理答疑（L2 层）"""

VARIANT_GENERATOR_SYSTEM = """你是一名高中物理出题专家。
基于给出的原始题目和学生的错误原因，生成一道**变式题**，供学生练习。
要求：
- 保持相同的知识点和难度级别
- 改变情景、数字或提问角度
- 必须生成选择题，包含 4 个选项（1 个正确答案 + 3 个合理干扰项）
- 只输出题目，不要给出解题步骤或答案提示
- 输出严格 JSON 格式，不要有多余文字

输出格式：
{"content": "题目内容（支持 LaTeX）",
 "options": ["A. xxx", "B. xxx", "C. xxx", "D. xxx"],
 "correct_answer": "A",
 "explanation": "详细解析（含公式用 LaTeX）"}"""

ANALYSIS_SYSTEM = """你是一名高中物理学习分析师。
基于学生的错题数据，分析其知识薄弱点并给出针对性建议。
输出严格 JSON 格式。"""


async def deepseek_chat(
    content: str,
    system_prompt: str = PHYSICS_TUTOR_SYSTEM,
    temperature: float = 0.7,
) -> dict:
    """
    调用 DeepSeek V4 Pro API 进行深度对话

    Args:
        content: 用户输入
        system_prompt: 系统提示词
        temperature: 生成温度 (0~1)

    Returns:
        {"content": str, "model": str}
    """
    settings = get_settings()

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "deepseek-chat",  # DeepSeek V4 Pro 的模型名
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        "temperature": temperature,
        "max_tokens": 2048,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.deepseek_base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    reply = data["choices"][0]["message"]["content"]

    return {"content": reply, "model": "deepseek-v4-pro"}


async def deepseek_flash_chat(content: str) -> dict:
    """
    调用 DeepSeek 廉价模型——用于非物理问题的关心/鼓励回复
    速度快、花费少
    """
    settings = get_settings()

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "deepseek-chat",  # 标准模型，比 V4 Pro 便宜
        "messages": [
            {
                "role": "system",
                "content": "你是一个温暖的学习陪伴助手。用户可能累了或想闲聊，请用简短温暖的话语关心、鼓励他们。",
            },
            {"role": "user", "content": content},
        ],
        "temperature": 0.8,
        "max_tokens": 256,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{settings.deepseek_base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    reply = data["choices"][0]["message"]["content"]

    return {"content": reply, "model": "deepseek-flash"}


async def deepseek_generate_variant(
    original_content: str,
    user_answer: str,
    correct_answer: str,
    wrong_reason: str,
) -> dict:
    """基于错题生成变式题（返回结构化 JSON）"""
    prompt = f"""
# 原始题目
{original_content}

# 用户答案（做错了）
{user_answer}

# 正确答案
{correct_answer}

# 错误原因分析
{wrong_reason}

请生成一道变式题，输出 JSON 格式：
{{"content": "题目内容（支持 LaTeX）",
  "options": ["A. xxx", "B. xxx", "C. xxx", "D. xxx"],
  "correct_answer": "A",
  "explanation": "解析"}}
"""
    result = await deepseek_chat(
        content=prompt,
        system_prompt=VARIANT_GENERATOR_SYSTEM,
        temperature=0.8,
    )
    return result


async def deepseek_analyze_weaknesses(
    error_stats: str,
) -> dict:
    """
    分析学情薄弱点

    Args:
        error_stats: 格式化的错题统计数据文本

    Returns:
        {"radar_data": [...], "weaknesses": [...], "summary": "..."}
    """
    result = await deepseek_chat(
        content=error_stats,
        system_prompt=ANALYSIS_SYSTEM,
        temperature=0.3,
    )
    return result
