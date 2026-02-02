# input_normalizer.py
from datetime import datetime, timedelta

def normalize_input(user_text: str):
    """
    返回一个 dict：
    {
        "intent": "clock_query" | "fragment_record" | "unknown",
        "resolved_date": "YYYY-MM-DD" | None,
        "clean_text": 原始用户输入
    }
    """

    text = user_text.strip()

    # 1️⃣ 意图判断（最简单版本）
    if "打卡" in text:
        intent = "clock_query"
    elif "记录" in text or "完成" in text:
        intent = "fragment_record"
    else:
        intent = "unknown"

    # 2️⃣ 相对日期处理
    today = datetime.now().date()
    resolved_date = None

    if "今天" in text:
        resolved_date = today.strftime("%Y-%m-%d")
    elif "昨天" in text:
        resolved_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif "前天" in text:
        resolved_date = (today - timedelta(days=2)).strftime("%Y-%m-%d")

    return {
        "intent": intent,
        "resolved_date": resolved_date,
        "clean_text": text,
    }
