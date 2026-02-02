# 独立测试脚本：验证路由逻辑
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from input_normalizer import normalize_input

def test_routing(text, author):
    """模拟路由逻辑"""
    norm = normalize_input(text)
    clean_text = norm.get("clean_text", text)

    print(f"\n输入: text='{text}', clean_text='{clean_text}'")

    # reject
    if any(keyword in clean_text for keyword in ["日报", "周报", "总结"]):
        print(f"  → action: reject")
        return "reject"

    # confirm
    elif "打卡" in clean_text:
        print(f"  → action: confirm")
        return "confirm"

    # query
    elif any(keyword in clean_text for keyword in ["今天做了啥", "今天干了啥", "今天做了什么", "做了啥", "干了啥", "做了什么"]):
        print(f"  → action: query (matched pattern)")
        return "query"

    # record（需要事实门槛）
    else:
        fact_verbs = ["完成", "执行", "编写", "测试", "修复", "实现", "开发", "部署", "设计"]
        has_fact_verb = any(verb in clean_text for verb in fact_verbs)
        has_content = len(clean_text.strip()) > 3
        is_question = any(marker in clean_text for marker in ["？", "?", "啥", "什么", "吗", "呢"])
        can_record = has_fact_verb and has_content and not is_question

        print(f"  → fact_verb={has_fact_verb}, content={has_content}, question={is_question}, can_record={can_record}")

        if can_record:
            print(f"  → action: record")
            return "record"
        else:
            print(f"  → action: query (fallback)")
            return "query"


if __name__ == "__main__":
    print("=== 路由逻辑测试 ===")
    test_routing("做了啥", "test")
    test_routing("今天完成了WMS用例执行", "张三")
    test_routing("今天做了啥", "all")
