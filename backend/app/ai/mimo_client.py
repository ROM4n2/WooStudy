"""Mimo API 封装——负责多模态识图与基础简答（L1 层）"""

import httpx
from typing import Optional

from app.config import get_settings


async def mimo_chat(
    content: str,
    image_base64: Optional[str] = None,
) -> dict:
    """
    调用 Mimo API 进行对话/识图

    Args:
        content: 用户文字输入
        image_base64: Base64 编码的图片（可选）

    Returns:
        {"content": str, "confidence": float}
    """
    settings = get_settings()

    headers = {
        "Authorization": f"Bearer {settings.mimo_api_key}",
        "Content-Type": "application/json",
    }

    # 构建消息体（Mimo 兼容 OpenAI 格式）
    system_content = (
        "你是一名高中物理 AI 导师。只回答物理学习相关问题。"
        "如果用户提问与物理完全无关，请关心用户是否累了、给予鼓励，不要回答无关内容。"
        "涉及公式时，请使用标准 LaTeX 格式：行内公式用 $...$，独立公式用 $$...$$。"
    )
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": []},
    ]

    # user 消息是 messages[1]
    user_content_list = messages[1]["content"]

    # 添加文字
    if content:
        user_content_list.append({"type": "text", "text": content})

    # 添加图片（如果存在）
    if image_base64:
        user_content_list.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}"
            },
        })

    payload = {
        "model": "mimo-v2.5",  # Omni 系列，支持全模态理解（文本+图片）
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.3,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.mimo_base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    # 解析返回（兼容 OpenAI 格式）
    reply = data["choices"][0]["message"]["content"]

    # 模拟置信度（生产环境应由 API 返回或通过文本分析得出）
    # 如果回答很短/含糊，降低置信度
    confidence = 0.85 if len(reply) > 50 else 0.5

    return {"content": reply, "confidence": confidence}


async def mimo_flash_chat(content: str, system_prompt: str | None = None) -> dict:
    """
    调用 Mimo Flash 廉价模型——速度快、花费少

    Args:
        content: 用户输入
        system_prompt: 自定义系统提示词（不传时默认陪伴助手）
    """
    settings = get_settings()

    headers = {
        "Authorization": f"Bearer {settings.mimo_api_key}",
        "Content-Type": "application/json",
    }

    if system_prompt is None:
        system_prompt = "你是一个温暖的学习陪伴助手。用户可能累了或想闲聊，请用简短温暖的话语关心、鼓励他们。"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content},
    ]

    payload = {
        "model": "mimo-v2-flash",  # Flash 系列，便宜快速
        "messages": messages,
        "max_tokens": 256,
        "temperature": 0.8,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{settings.mimo_base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    reply = data["choices"][0]["message"]["content"]

    return {"content": reply, "confidence": 0.95}
