"""Mock AI 客户端——开发阶段替代真实 API 调用，避免产生 API 费用"""

import json
import random


# 非物理关键词——用于模拟检测
_NON_PHYSICS_KEYWORDS = ["你好", "吃饭", "天气", "电影", "音乐", "游戏", "累", "休息"]


async def mock_chat(
    content: str,
    image_base64: str | None = None,
) -> dict:
    """模拟 Mimo 的 L1 回答"""
    # 模拟非物理问题检测
    for kw in _NON_PHYSICS_KEYWORDS:
        if kw in content:
            return {
                "content": "看起来你有点累了？要不要休息一会儿？学物理需要保持好状态哦！💪",
                "confidence": 0.95,
            }

    mock_responses = [
        "这道题考察的是牛顿第二定律。根据 F=ma，我们可以先分析物体的受力情况……",
        "根据动能定理，合外力做的功等于动能的变化量。在这个问题中……",
        "电磁感应现象中，感应电动势的大小由法拉第定律 ε = -dΦ/dt 决定……",
        "光的折射遵循斯涅尔定律 n₁sinθ₁ = n₂sinθ₂。当光从光密介质进入光疏介质时……",
    ]

    # 模拟：如果带了图片，置信度略降
    confidence = 0.75 if image_base64 else 0.85

    return {
        "content": random.choice(mock_responses),
        "confidence": confidence,
    }


async def mock_deepseek(
    content: str,
    system_prompt: str = "",
) -> dict:
    """模拟 DeepSeek 的 L2 深度回答"""
    # 模拟非物理问题检测
    for kw in _NON_PHYSICS_KEYWORDS:
        if kw in content:
            return {
                "content": "看起来你有点累了？要不要先休息一下？\n\n学习物理需要专注，适当放松反而效率更高哦！✨\n\n需要我陪你聊聊，还是给你加油打气？💪",
                "model": "mock(deepseek-v4-pro)",
            }

    deep_responses = [
        "## 分步解析\n\n### 第一步：分析题意\n题目给出了物体的质量 m=2kg，初速度 v₀=3m/s……\n\n### 第二步：选择定理\n由于涉及力和位移，优先考虑动能定理……\n\n### 第三步：列式求解\n由动能定理：$W = \\Delta E_k = \\frac{1}{2}mv^2 - \\frac{1}{2}mv_0^2$\n代入数据……\n\n### 第四步：检验\n从量纲和数量级判断结果合理。",
        "## 知识点梳理\n\n本题核心考点：**楞次定律**和**法拉第电磁感应定律**。\n\n### 关键公式\n$$\\mathcal{E} = -\\frac{d\\Phi_B}{dt}$$\n\n### 注意事项\n- 感应电流的方向总使自身产生的磁场阻碍原磁场的变化\n- 计算时注意符号代表的是方向而非大小",
    ]
    return {
        "content": random.choice(deep_responses),
        "model": "mock(deepseek-v4-pro)",
    }


async def mock_generate_variant(
    original_content: str,
    user_answer: str,
    correct_answer: str,
    wrong_reason: str,
) -> dict:
    """模拟变式题生成（返回有效 JSON）"""
    subjects = ["力学", "电学", "光学"]
    subject = subjects[hash(original_content) % len(subjects)]

    mock_variants = {
        "力学": {
            "content": "一个质量为 2kg 的物体在水平面上受到 10N 的水平拉力，"
                       "物体与地面的动摩擦因数为 0.2，求物体运动的加速度？\n\n"
                       "（$g=10m/s^2$）",
            "options": [
                "A. $3m/s^2$",
                "B. $4m/s^2$",
                "C. $5m/s^2$",
                "D. $6m/s^2$",
            ],
            "correct_answer": "A",
            "explanation": "由牛顿第二定律：$F - \\mu mg = ma$\n"
                           "$a = (F - \\mu mg)/m = (10 - 0.2\\times2\\times10)/2 = 3m/s^2$",
        },
        "电学": {
            "content": "如图所示电路，电源电动势 E=12V，内阻 r=1Ω，"
                       "外电路电阻 R=5Ω，求电路中的电流强度？",
            "options": [
                "A. 1A",
                "B. 2A",
                "C. 3A",
                "D. 4A",
            ],
            "correct_answer": "B",
            "explanation": "由闭合电路欧姆定律：$I = E/(R+r) = 12/(5+1) = 2A$",
        },
        "光学": {
            "content": "一束光从空气射入水中，入射角为 45°，水的折射率为 1.33，"
                       "求折射角的大小？",
            "options": [
                "A. $32.1°$",
                "B. $36.5°$",
                "C. $41.2°$",
                "D. $48.5°$",
            ],
            "correct_answer": "A",
            "explanation": "由斯涅尔定律：$n_1\\sin\\theta_1 = n_2\\sin\\theta_2$\n"
                           "$\\sin\\theta_2 = (1\\times\\sin45°)/1.33 ≈ 0.532$\n"
                           "$\\theta_2 = \\arcsin(0.532) ≈ 32.1°$",
        },
    }

    v = mock_variants[subject]
    return {
        "content": v["content"],
        "options": v["options"],
        "correct_answer": v["correct_answer"],
        "explanation": v["explanation"],
        "model": "mock(deepseek-v4-pro)",
    }


async def mock_analyze_weaknesses(error_stats: str) -> dict:
    """模拟学情分析"""
    return {
        "radar_data": [
            {"subject": "力学", "correct_rate": 0.65, "question_count": 20},
            {"subject": "电学", "correct_rate": 0.80, "question_count": 15},
            {"subject": "热学", "correct_rate": 0.90, "question_count": 5},
            {"subject": "光学", "correct_rate": 0.50, "question_count": 8},
            {"subject": "近代物理", "correct_rate": 0.70, "question_count": 6},
        ],
        "weaknesses": [
            {
                "subject": "力学",
                "concept": "牛顿第二定律的应用",
                "suggestion": "建议重点复习受力分析步骤：先重力、再弹力、后摩擦力。多做斜面-滑块的经典题型。",
            },
            {
                "subject": "光学",
                "concept": "光的折射与全反射",
                "suggestion": "掌握临界角公式 $\\sin C = 1/n$，熟悉光密/光疏介质的判断。",
            },
        ],
        "summary": "整体处于中等水平。力学和光学是薄弱环节，建议集中突破。"
                   "电学和热学掌握较好，可以进入拔高训练。",
    }
