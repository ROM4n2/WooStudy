"""双模型调度器——实现 L1 (Mimo) → L2 (DeepSeek) 的分层调度逻辑

调度策略：
1. 所有请求先进入 Mimo（L1 层）
2. 如果 Mimo 置信度 < 阈值，自动 fallback 到 DeepSeek（L2 层）
3. 如果用户开启了"深度优先模式"，跳过 Mimo，直接请求 DeepSeek
4. Mock 模式下所有请求走 Mock 客户端
5. 非物理话题自动走廉价 Flash 模型，降低费用
"""

import re
from typing import Optional

from app.config import get_settings
from app.ai.mimo_client import mimo_chat, mimo_flash_chat
from app.ai.deepseek_client import deepseek_chat, deepseek_flash_chat, deepseek_generate_variant, deepseek_analyze_weaknesses
from app.ai.mock_client import (
    mock_chat,
    mock_deepseek,
    mock_generate_variant,
    mock_analyze_weaknesses,
)

# 非物理话题关键词快速预检——命中后走廉价模型
_NON_PHYSICS_PATTERNS = [
    r"(你好|嗨|hi|hello|hey)",
    r"(累|休息|睡觉|困|疲惫|疲)",
    r"(加油|鼓励|打气|坚持)",
    r"(天气|下雨|打雷|刮风|温度)",
    r"(吃[饭了]|喝[水茶]|饿)",
    r"(电影|音乐|游戏|综艺|节目)",
    r"(新闻|八卦|热搜|头条)",
    r"(想|聊|陪|说|谈)[^理]*[^物]",
]


def _is_likely_non_physics(content: str) -> bool:
    """快速关键词预检——判断是否可能为非物理话题"""
    for pattern in _NON_PHYSICS_PATTERNS:
        if re.search(pattern, content):
            return True
    return False


async def dispatch_chat(
    content: str,
    image_base64: Optional[str] = None,
    deep_mode: bool = False,
) -> dict:
    """
    L1→L2 调度：根据置信度和模式决定走哪个模型

    Args:
        content: 用户文字输入
        image_base64: Base64 图片（可选）
        deep_mode: 用户设置中的"深度优先模式"开关

    Returns:
        {"content": str, "model_used": str, "confidence": float}
    """
    settings = get_settings()

    # ---------- 快速预检：非物理话题 → 廉价的 Flash 模型 ----------
    if not image_base64 and _is_likely_non_physics(content):
        print(f"[Dispatcher] 非物理话题，走 Flash 廉价模型")
        if settings.mock_mode:
            result = await mock_chat(content)
        else:
            # 优先用 Mimo Flash（比 DeepSeek 更便宜）
            result = await mimo_flash_chat(content)
        return {
            "content": result["content"],
            "model_used": "mimo-v2-flash",
            "confidence": 0.95,
        }

    # ---------- Mock 模式：直接返回假数据 ----------
    if settings.mock_mode:
        # 模拟 L1→L2 效果
        if deep_mode:
            result = await mock_deepseek(content)
            return {
                "content": result["content"],
                "model_used": "mock(deepseek-v4-pro)",
                "confidence": 0.95,
            }
        else:
            result = await mock_chat(content, image_base64)
            return {
                "content": result["content"],
                "model_used": "mock(mimo)",
                "confidence": result["confidence"],
            }

    # ---------- 深度优先模式：直达 DeepSeek ----------
    if deep_mode:
        result = await deepseek_chat(content)
        return {
            "content": result["content"],
            "model_used": "deepseek-v4-pro",
            "confidence": 0.95,
        }

    # ---------- 标准模式：L1 → L2 fallback ----------
    try:
        mimo_result = await mimo_chat(content, image_base64)
        confidence = mimo_result["confidence"]

        if confidence >= settings.mimo_confidence_threshold:
            # Mimo 置信度足够，直接返回
            return {
                "content": mimo_result["content"],
                "model_used": "mimo",
                "confidence": confidence,
            }

        # Mimo 置信度不足，调用 DeepSeek 深度回答
        deepseek_prompt = (
            f"用户提问：{content}\n\n"
            f"初步分析摘要：{mimo_result['content']}\n\n"
            f"请提供更深入、更准确的物理答疑。"
        )
    except Exception as e:
        print(f"[Dispatcher] Mimo 调用失败，降级到 DeepSeek: {e}")
        deepseek_prompt = content
    deepseek_result = await deepseek_chat(deepseek_prompt)

    return {
        "content": deepseek_result["content"],
        "model_used": "deepseek-v4-pro",
        "confidence": 0.95,
    }


async def dispatch_optimize_prompt(raw_text: str) -> dict:
    """
    优化用户提示词——用廉价 Flash 模型将杂乱提问重写为清晰有条理的提问

    Args:
        raw_text: 用户原始输入

    Returns:
        {"content": str} 优化后的文本
    """
    settings = get_settings()

    system_prompt = (
        "你是一名高中物理学习助手。请帮学生把下面这段提问整理得更清晰有条理："
        "保持原意不改变知识点内容，拆分为逻辑清晰的步骤，用简洁准确的中文复述。"
        "只输出优化后的提问，不要加任何评语或解释。"
    )

    if settings.mock_mode:
        return {"content": raw_text}

    try:
        result = await mimo_flash_chat(raw_text, system_prompt=system_prompt)
        optimized = result["content"].strip()
        # 防止模型添加额外评语，截取第1段
        if len(optimized) > 500:
            optimized = optimized[:500]
        return {"content": optimized}
    except Exception as e:
        print(f"[Dispatcher] 提示词优化失败，返回原文: {e}")
        return {"content": raw_text}


async def dispatch_followup_chat(
    history: list[dict],
    new_content: str,
    deep_mode: bool = False,
) -> dict:
    """
    追问模式：先总结历史对话，再结合当前问题请求 AI

    流程：
    1. 用 Flash 模型将最近 5 轮对话总结为 1-2 句
    2. 将总结 + 当前问题发给主模型

    Args:
        history: 最近对话列表 [{"role": str, "content": str}, ...]
        new_content: 当前用户输入
        deep_mode: 是否深度优先

    Returns:
        {"content": str, "model_used": str, "summary_for_persist": str}
    """
    settings = get_settings()

    # 构造供总结的文本
    history_text = "\n".join(
        f"{'学生' if m['role'] == 'user' else '老师'}: {m['content'][:200]}"
        for m in history[-5:]
    )

    # 用 Flash 模型总结
    if settings.mock_mode:
        summary = f"学生正在持续提问物理问题，已讨论：{new_content[:30]}"
    else:
        try:
            summary_result = await mimo_flash_chat(
                f"请用一句话总结以下师生对话中已讨论的物理知识点和学生当前水平。\n\n{history_text}\n\n只输出总结，不要多余文字。"
            )
            summary = summary_result["content"][:300]
        except Exception as e:
            print(f"[Dispatcher] 追问总结失败: {e}")
            summary = f"学生提问了物理相关问题。"

    # 构造完整 prompt
    full_prompt = f"[上下文摘要]\n{summary}\n\n[当前提问]\n{new_content}"

    if settings.mock_mode:
        result = await mock_deepseek(full_prompt) if deep_mode else await mock_chat(full_prompt)
        return {
            "content": result["content"],
            "model_used": "mock(mimo)",
            "confidence": 0.95,
            "summary_for_persist": summary,
        }

    if deep_mode:
        result = await deepseek_chat(full_prompt)
        return {
            "content": result["content"],
            "model_used": "deepseek-v4-pro",
            "confidence": 0.95,
            "summary_for_persist": summary,
        }

    try:
        result = await mimo_chat(full_prompt)
        confidence = result.get("confidence", 0.85)
        if confidence >= settings.mimo_confidence_threshold:
            return {
                "content": result["content"],
                "model_used": "mimo",
                "confidence": confidence,
                "summary_for_persist": summary,
            }
        deepseek_prompt = f"上下文：{summary}\n\n用户提问：{new_content}\n\n初步分析：{result['content']}\n\n请提供更深入的回答。"
        result2 = await deepseek_chat(deepseek_prompt)
        return {
            "content": result2["content"],
            "model_used": "deepseek-v4-pro",
            "confidence": 0.95,
            "summary_for_persist": summary,
        }
    except Exception as e:
        print(f"[Dispatcher] 追问 Mimo 失败，降级到 DeepSeek: {e}")
        result = await deepseek_chat(full_prompt)
        return {
            "content": result["content"],
            "model_used": "deepseek-v4-pro",
            "confidence": 0.95,
            "summary_for_persist": summary,
        }


async def dispatch_generate_variant(
    original_content: str,
    user_answer: str,
    correct_answer: str,
    wrong_reason: str,
) -> dict:
    """变式出题：由 DeepSeek 或 Mock 生成"""
    settings = get_settings()

    if settings.mock_mode:
        return await mock_generate_variant(
            original_content, user_answer, correct_answer, wrong_reason
        )

    return await deepseek_generate_variant(
        original_content, user_answer, correct_answer, wrong_reason
    )


async def dispatch_analyze(error_stats: str) -> dict:
    """学情分析：由 DeepSeek 或 Mock 分析"""
    settings = get_settings()

    if settings.mock_mode:
        return await mock_analyze_weaknesses(error_stats)

    return await deepseek_analyze_weaknesses(error_stats)
