"""双模型调度器——实现 L1 (Mimo) → L2 (DeepSeek) 的分层调度逻辑

所有 API Key 由上层（Service）传入，不再从 config 读取。
如果用户未提供 Key 且服务器也无备用 Key，返回友好错误。
"""
import re
import json
from typing import Optional

from app.config import get_settings
from app.ai.mimo_client import mimo_chat, mimo_flash_chat
from app.ai.deepseek_client import (
    deepseek_chat,
    deepseek_flash_chat,
    deepseek_generate_variant,
    deepseek_analyze_weaknesses,
)
from app.ai.mock_client import (
    mock_chat,
    mock_deepseek,
    mock_generate_variant,
    mock_analyze_weaknesses,
)

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

NO_KEY_ERROR = "请先在「设置」中填写你的 Mimo 和 DeepSeek API Key，然后才能使用 AI 功能 🎯"


def _is_likely_non_physics(content: str) -> bool:
    for pattern in _NON_PHYSICS_PATTERNS:
        if re.search(pattern, content):
            return True
    return False


def _resolve_keys(mimo_key: str, deepseek_key: str) -> tuple:
    """解析 API Key：优先用用户传入的，其次用服务器备用 Key"""
    settings = get_settings()
    mk = mimo_key or settings.mimo_api_key
    dk = deepseek_key or settings.deepseek_api_key
    return mk, dk


async def dispatch_chat(
    content: str,
    image_base64: Optional[str] = None,
    deep_mode: bool = False,
    mimo_key: str = "",
    deepseek_key: str = "",
) -> dict:
    """L1→L2 调度主入口"""
    settings = get_settings()
    mimo_key, deepseek_key = _resolve_keys(mimo_key, deepseek_key)

    # 非物理话题 → Flash 廉价模型
    if not image_base64 and _is_likely_non_physics(content):
        print(f"[Dispatcher] 非物理话题，走 Flash 廉价模型")
        if settings.mock_mode:
            result = await mock_chat(content)
        else:
            key = mimo_key or deepseek_key
            if not key:
                return {"content": NO_KEY_ERROR, "model_used": "none", "confidence": 0}
            result = await mimo_flash_chat(content, api_key=key)
        return {"content": result["content"], "model_used": "mimo-v2-flash", "confidence": 0.95}

    # Mock 模式
    if settings.mock_mode:
        if deep_mode:
            result = await mock_deepseek(content)
            return {"content": result["content"], "model_used": "mock(deepseek-v4-pro)", "confidence": 0.95}
        result = await mock_chat(content, image_base64)
        return {"content": result["content"], "model_used": "mock(mimo)", "confidence": result["confidence"]}

    # 深度优先模式
    if deep_mode:
        if not deepseek_key:
            return {"content": NO_KEY_ERROR, "model_used": "none", "confidence": 0}
        result = await deepseek_chat(content, api_key=deepseek_key)
        return {"content": result["content"], "model_used": "deepseek-v4-pro", "confidence": 0.95}

    # 标准模式：L1 → L2 fallback
    if not mimo_key and not deepseek_key:
        return {"content": NO_KEY_ERROR, "model_used": "none", "confidence": 0}

    try:
        mimo_result = await mimo_chat(content, image_base64, api_key=mimo_key)
        confidence = mimo_result["confidence"]
        if confidence >= settings.mimo_confidence_threshold:
            return {"content": mimo_result["content"], "model_used": "mimo", "confidence": confidence}

        # Fallback
        if not deepseek_key:
            return {"content": mimo_result["content"], "model_used": "mimo", "confidence": confidence}
        deepseek_prompt = f"用户提问：{content}\n\n初步分析摘要：{mimo_result['content']}\n\n请提供更深入、更准确的物理答疑。"
    except Exception as e:
        print(f"[Dispatcher] Mimo 调用失败，降级到 DeepSeek: {e}")
        if not deepseek_key:
            return {"content": NO_KEY_ERROR, "model_used": "none", "confidence": 0}
        deepseek_prompt = content

    deepseek_result = await deepseek_chat(deepseek_prompt, api_key=deepseek_key)
    return {"content": deepseek_result["content"], "model_used": "deepseek-v4-pro", "confidence": 0.95}


async def dispatch_optimize_prompt(
    raw_text: str,
    mimo_key: str = "",
    deepseek_key: str = "",
) -> dict:
    """优化用户提示词"""
    settings = get_settings()
    mimo_key, deepseek_key = _resolve_keys(mimo_key, deepseek_key)

    if settings.mock_mode:
        return {"content": raw_text}

    key = mimo_key or deepseek_key
    if not key:
        return {"content": raw_text}

    system_prompt = "你是一名高中物理学习助手。请帮学生把下面这段提问整理得更清晰有条理：保持原意不改变知识点内容，拆分为逻辑清晰的步骤，用简洁准确的中文复述。只输出优化后的提问，不要加任何评语或解释。"

    try:
        result = await mimo_flash_chat(raw_text, system_prompt=system_prompt, api_key=key)
        optimized = result["content"].strip()
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
    mimo_key: str = "",
    deepseek_key: str = "",
) -> dict:
    """追问模式"""
    settings = get_settings()
    mimo_key, deepseek_key = _resolve_keys(mimo_key, deepseek_key)

    history_text = "\n".join(
        f"{'学生' if m['role'] == 'user' else '老师'}: {m['content'][:200]}"
        for m in history[-5:]
    )

    # 用 Flash 模型总结
    if settings.mock_mode:
        summary = f"学生正在持续提问物理问题，已讨论：{new_content[:30]}"
    else:
        key = mimo_key or deepseek_key
        if not key:
            summary = f"学生提问了物理相关问题。"
        else:
            try:
                summary_result = await mimo_flash_chat(
                    f"请用一句话总结以下师生对话中已讨论的物理知识点和学生当前水平。\n\n{history_text}\n\n只输出总结，不要多余文字。",
                    api_key=key,
                )
                summary = summary_result["content"][:300]
            except:
                summary = f"学生提问了物理相关问题。"

    full_prompt = f"[上下文摘要]\n{summary}\n\n[当前提问]\n{new_content}"

    if settings.mock_mode:
        result = await mock_deepseek(full_prompt) if deep_mode else await mock_chat(full_prompt)
        return {"content": result["content"], "model_used": "mock(mimo)", "confidence": 0.95, "summary_for_persist": summary}

    if deep_mode:
        if not deepseek_key:
            return {"content": NO_KEY_ERROR, "model_used": "none", "confidence": 0, "summary_for_persist": summary}
        result = await deepseek_chat(full_prompt, api_key=deepseek_key)
        return {"content": result["content"], "model_used": "deepseek-v4-pro", "confidence": 0.95, "summary_for_persist": summary}

    if not mimo_key:
        if deepseek_key:
            result = await deepseek_chat(full_prompt, api_key=deepseek_key)
            return {"content": result["content"], "model_used": "deepseek-v4-pro", "confidence": 0.95, "summary_for_persist": summary}
        return {"content": NO_KEY_ERROR, "model_used": "none", "confidence": 0, "summary_for_persist": summary}

    try:
        result = await mimo_chat(full_prompt, api_key=mimo_key)
        confidence = result.get("confidence", 0.85)
        if confidence >= settings.mimo_confidence_threshold:
            return {"content": result["content"], "model_used": "mimo", "confidence": confidence, "summary_for_persist": summary}
        if deepseek_key:
            deepseek_prompt = f"上下文：{summary}\n\n用户提问：{new_content}\n\n初步分析：{result['content']}\n\n请提供更深入的回答。"
            result2 = await deepseek_chat(deepseek_prompt, api_key=deepseek_key)
            return {"content": result2["content"], "model_used": "deepseek-v4-pro", "confidence": 0.95, "summary_for_persist": summary}
        return {"content": result["content"], "model_used": "mimo", "confidence": confidence, "summary_for_persist": summary}
    except:
        if deepseek_key:
            result = await deepseek_chat(full_prompt, api_key=deepseek_key)
            return {"content": result["content"], "model_used": "deepseek-v4-pro", "confidence": 0.95, "summary_for_persist": summary}
        return {"content": NO_KEY_ERROR, "model_used": "none", "confidence": 0, "summary_for_persist": summary}


async def dispatch_generate_variant(
    original_content: str,
    user_answer: str,
    correct_answer: str,
    wrong_reason: str,
    deepseek_key: str = "",
) -> dict:
    """变式出题"""
    settings = get_settings()
    _, deepseek_key = _resolve_keys("", deepseek_key)

    if settings.mock_mode:
        return await mock_generate_variant(original_content, user_answer, correct_answer, wrong_reason)

    if not deepseek_key:
        return {"error": NO_KEY_ERROR}

    return await deepseek_generate_variant(
        original_content, user_answer, correct_answer, wrong_reason,
        api_key=deepseek_key,
    )


async def dispatch_analyze(
    error_stats: str,
    deepseek_key: str = "",
) -> dict:
    """学情分析"""
    settings = get_settings()
    _, deepseek_key = _resolve_keys("", deepseek_key)

    if settings.mock_mode:
        return await mock_analyze_weaknesses(error_stats)

    if not deepseek_key:
        return {"error": NO_KEY_ERROR}

    return await deepseek_analyze_weaknesses(error_stats, api_key=deepseek_key)
