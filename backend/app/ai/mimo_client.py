"""Mimo API 封装——负责多模态识图与基础简答（L1 层）

所有 API Key 现在由调用方传入，不再从 config 读取。
"""
import httpx
from typing import Optional

MIMO_DEFAULT_BASE = "https://api.xiaomimimo.com/v1"


async def mimo_chat(
    content: str,
    image_base64: Optional[str] = None,
    api_key: str = "",
    base_url: str = MIMO_DEFAULT_BASE,
) -> dict:
    """
    调用 Mimo API 进行对话/识图
    Args:
        content: 用户文字输入
        image_base64: Base64 编码的图片（可选）
        api_key: 用户的 Mimo API Key
        base_url: API 基础地址
    Returns:
        {"content": str, "confidence": float}
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    system_content = (
        "你是一名高中物理 AI 导师。只回答物理学习相关问题。"
        "如果用户提问与物理完全无关，请关心用户是否累了、给予鼓励，不要回答无关内容。"
        "涉及公式时，请使用标准 LaTeX 格式：行内公式用 $...$，独立公式用 $$...$$。"
    )
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": []},
    ]

    user_content_list = messages[1]["content"]
    if content:
        user_content_list.append({"type": "text", "text": content})
    if image_base64:
        user_content_list.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
        })

    payload = {
        "model": "mimo-v2.5",
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.3,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    reply = data["choices"][0]["message"]["content"]
    confidence = 0.85 if len(reply) > 50 else 0.5
    return {"content": reply, "confidence": confidence}


async def mimo_flash_chat(
    content: str,
    system_prompt: str | None = None,
    api_key: str = "",
    base_url: str = MIMO_DEFAULT_BASE,
) -> dict:
    """
    调用 Mimo Flash 廉价模型
    Args:
        content: 用户输入
        system_prompt: 自定义系统提示词
        api_key: 用户的 Mimo API Key
        base_url: API 基础地址
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    if system_prompt is None:
        system_prompt = "你是一个温暖的学习陪伴助手。用户可能累了或想闲聊，请用简短温暖的话语关心、鼓励他们。"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content},
    ]

    payload = {
        "model": "mimo-v2-flash",
        "messages": messages,
        "max_tokens": 256,
        "temperature": 0.8,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    reply = data["choices"][0]["message"]["content"]
    return {"content": reply, "confidence": 0.95}
