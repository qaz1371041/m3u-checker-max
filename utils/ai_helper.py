import requests
import os
import re

# --- 配置区 ---
# 使用用户已部署的 Gemini 代理
API_ENDPOINT = "https://api.170909.xyz/v1beta/openai/chat/completions"
# 内存中确认工作的模型
MODEL = "gemma-4-31b-it"
# 【安全改进】从环境变量读取 API Key，绝对禁止硬编码在代码中
# 请在 GitHub Secrets 中添加 GEMINI_API_KEY
API_KEY = os.getenv("GEMINI_API_KEY", "")

def standardize_channel_name(raw_name: str) -> str:
    """
    调用 AI 将混乱的频道名称标准化。
    例如: "CCTV-1 超清 广东电信" -> "CCTV-1"
    "湖南卫视 (HD)" -> "湖南卫视"
    "CCTV-5 体育" -> "CCTV-5"
    "广东卫视-4K" -> "广东卫视"
    " CCTV-13 新闻 " -> "CCTV-13"
    """
    if not raw_name or not raw_name.strip():
        return raw_name

    # 简单的预处理：去除明显的冗余词，减少 Token 消耗
    clean_name = re.sub(r'(\s*\(.*?\)\s*|\s*\[.*?\]\s*|\s*[\-—].*$', '', raw_name).strip()
    
    # 构造 Prompt
    prompt = (
        f"You are an IPTV channel naming expert. Your task is to standardize the following channel name "
        f"into its most concise, official version. Remove all quality markers (4K, HD, 超清, 高清), "
        f"region markers (广东, 电信, 联通), and redundant descriptions.\n\n"
        f"Examples:\n"
        f"- 'CCTV-1 超清 广东电信' -> 'CCTV-1'\n"
        f"- '湖南卫视 (HD)' -> '湖南卫视'\n"
        f"- 'CCTV-5 体育' -> 'CCTV-5'\n"
        f"- '广东卫视-4K' -> '广东卫视'\n"
        f"- ' CCTV-13 新闻 ' -> 'CCTV-13'\n"
        f"- '浙江卫视 [高清]' -> '浙江卫视'\n\n"
        f"Input: '{raw_name}'\n"
        f"Output: (Return ONLY the standardized name, no explanation, no quotes)"
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}" if API_KEY else ""
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a precise data cleaning tool. Output only the final result."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0 # 确保输出稳定
    }

    try:
        # 设置较短的超时，防止主程序在测速时被 AI 阻塞
        response = requests.post(API_ENDPOINT, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            result = response.json()
            standardized = result['choices'][0]['message']['content'].strip()
            # 去除 AI 可能带的引号
            standardized = standardized.replace('"', '').replace("'", "")
            return standardized if standardized else raw_name
        else:
            # 如果没有 Key 或 API 报错，静默返回原名，不中断主流程
            return raw_name
    except Exception:
        # 任何异常直接返回原名，保证主流程不崩溃
        return raw_name
