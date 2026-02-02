# main.py
# v1.0 最小闭环：用户输入 -> 模型(带tools) -> (可选)执行tool -> (可选)二次模型整理 -> 输出
#
# 目标：先跑起来，行为可控、可回放、可测试
# 约束：只允许 tools.py 中定义的 5 个工具；其余输入必须兜底，不触发工具

import os
from datetime import datetime, date

import json
import os
from typing import Any, Dict, List, Optional, Tuple
from input_normalizer import normalize_input

from zhipuai import ZhipuAI

from tools import function_schemas, dispatch_tool_call


MODEL_NAME = os.getenv("ZHIPU_MODEL", "glm-4.5")
API_KEY = os.getenv("ZHIPU_API_KEY", "")


def get_today_str() -> str:
    """统一定义 today，避免散落 date.today()"""
    return date.today().strftime("%Y-%m-%d")


SYSTEM_PROMPT = """
你是一个“个人工作风险防御”助手，核心目标是：记录干净事实碎片、执行打卡确认/超时记录、查询碎片与打卡状态。

严格规则（必须遵守）：
1) 你只能通过工具执行“写入/查询”动作。允许的工具只有：
   - record_fragment
   - get_fragments_by_date
   - confirm_clock_event
   - mark_clock_timeout
   - get_clock_status
2) 只有当用户输入满足以下类型时才可触发工具：
   - 干净事实碎片（清晰、可复用、无辱骂/强情绪/纯评价）-> record_fragment
   - 碎片查询（回顾/梳理/今天做了啥）-> get_fragments_by_date
   - 打卡状态查询（我打卡了吗）-> get_clock_status
   - 明确打卡确认（帮我打卡/我已打卡）-> confirm_clock_event
   - 超时记录由系统触发（如用户要求模拟也可）-> mark_clock_timeout
3) 情绪/吐槽/辱骂/越界生成（写日报/写用例）等：不要触发任何工具。只做简短、克制的澄清或拒绝，并引导用户给出“干净事实”或“明确查询/确认”。

输出要求：
- 若触发工具：先触发工具，再基于工具返回结果给出简短确认。
- 若不触发工具：简短回应即可，不要长篇大论。
【日期与时间默认规则】
- 用户语义为“今天/现在”且未提供具体日期：必须直接使用今天日期调用工具，不得追问。
- 只有在相对时间（昨天/前天/上周）且无法确定具体日期时，才允许追问一次。
- 不要为了信息完整性而延迟工具调用。

示例：
用户：今天完成了WMS用例执行
助手：直接调用 record_fragment(content="完成WMS用例执行", occurred_date=今天, source="user")
- 对于状态查询类问题（如“今天打卡了吗 / 查询打卡状态”），若未提供日期但语义明确为“今天”，必须直接使用今天日期调用查询工具，不得追问。
【相对日期处理规则】
- 对于“昨天 / 前天”这类明确的相对日期，允许直接自动换算为具体日期并调用工具，不需要向用户追问。
- 换算规则：
  - 昨天 = 今天 - 1 天
  - 前天 = 今天 - 2 天
- 只有在相对日期不明确（如“上周”“最近几天”）时，才允许追问。

""".strip()


def _extract_tool_calls(resp: Any) -> List[Dict[str, Any]]:
    """
    兼容性提取：尽量适配不同 SDK 返回结构。
    目标结构：[{id, function:{name, arguments}}...]
    """
    try:
        msg = resp.choices[0].message
    except Exception:
        return []

    # 常见：message.tool_calls
    tool_calls = getattr(msg, "tool_calls", None)
    if tool_calls:
        # tool_calls 可能是对象列表，转成 dict
        out = []
        for tc in tool_calls:
            if isinstance(tc, dict):
                out.append(tc)
            else:
                out.append({
                    "id": getattr(tc, "id", None),
                    "function": {
                        "name": getattr(getattr(tc, "function", None), "name", None),
                        "arguments": getattr(getattr(tc, "function", None), "arguments", None),
                    }
                })
        return out

    # 有些 SDK：message.tool_call / function_call（单个）
    fc = getattr(msg, "function_call", None) or getattr(msg, "tool_call", None)
    if fc:
        if isinstance(fc, dict):
            return [{"id": fc.get("id"), "function": {"name": fc.get("name"), "arguments": fc.get("arguments")}}]
        return [{"id": getattr(fc, "id", None), "function": {"name": getattr(fc, "name", None), "arguments": getattr(fc, "arguments", None)}}]

    return []


def _to_tool_message(tool_call_id: str, name: str, result: Any) -> Dict[str, Any]:
    """
    将工具执行结果回灌给模型（OpenAI 兼容格式；智谱通常也能接受类似结构）。
    """
    return {
        "role": "tool",
        "tool_call_id": tool_call_id or "",
        "name": name,
        "content": json.dumps(result, ensure_ascii=False),
    }


def call_model(client: ZhipuAI, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Any:
    return client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )


def run_once(client: ZhipuAI, user_text: str) -> str:
    # ✅ 0) 先做输入归一化（意图 + 相对日期）
    norm = normalize_input(user_text)
    print("NORMALIZED:", norm)  # 调试用：看解析结果
    today_str = get_today_str()
    print("TODAY:", today_str)  # 调试用：看系统今天

    # ✅ 1) 动态注入“当前日期 + 已解析日期/意图”，让模型别猜
    system_prompt_runtime = SYSTEM_PROMPT + "\n"
    system_prompt_runtime += f"【当前日期】{today_str}\n"

    if norm.get("resolved_date"):
        system_prompt_runtime += f"【已解析日期】{norm['resolved_date']}\n"
    if norm.get("intent") and norm["intent"] != "unknown":
        system_prompt_runtime += f"【已识别意图】{norm['intent']}\n"

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt_runtime},
        {"role": "user", "content": norm.get("clean_text", user_text)},
    ]

    # 2) 第一次模型：决定是否调用工具
    resp1 = call_model(client, messages, function_schemas)

    tool_calls = _extract_tool_calls(resp1)
    if not tool_calls:
        try:
            return resp1.choices[0].message.content or ""
        except Exception:
            return ""

    last_tool_results = []

    # 3) 执行工具
    for tc in tool_calls:
        tc_id = (tc.get("id") or "") if isinstance(tc, dict) else ""
        fn = tc.get("function", {}) if isinstance(tc, dict) else {}
        name = fn.get("name")
        raw_args = fn.get("arguments") or "{}"

        if isinstance(raw_args, str):
            try:
                args = json.loads(raw_args)
            except Exception:
                args = {}
        elif isinstance(raw_args, dict):
            args = raw_args
        else:
            args = {}

        tool_result = dispatch_tool_call(name=name, args=args)
        last_tool_results.append((name, tool_result))
        messages.append(_to_tool_message(tool_call_id=tc_id, name=name or "", result=tool_result))

    # 4) 第二次模型：基于工具结果答复
    resp2 = call_model(client, messages, function_schemas)
    try:
        text = resp2.choices[0].message.content or ""
    except Exception:
        text = ""

    if text.strip():
        return text

    # 5) 兜底：模型沉默时自己说话
    if len(last_tool_results) == 1:
        name, result = last_tool_results[0]
        if name == "get_clock_status":
            d = result.get("date", "该日期")
            items = result.get("items") or result.get("item") or {}
            if not items:
                return f"根据查询结果，{d} 没有打卡记录。"
            return f"根据查询结果，{d} 打卡状态：{json.dumps(items, ensure_ascii=False)}"

    return "已完成操作（模型未返回文本）。"


def run_once_with_structured_response(
    client: ZhipuAI,
    user_text: str,
    author: str
) -> Dict[str, Any]:
    """
    返回结构化响应，供 API 调用

    确定性路由规则（优先级从高到低）：
    1. reject: 包含"日报/周报/总结"
    2. confirm: 包含"打卡"
    3. query: 包含查询模式 或 不满足 record 事实门槛
    4. record: 满足事实门槛（明确动词 + 非空内容）
    """
    from tools import get_fragments_by_date, record_fragment

    # 1) 归一化输入
    norm = normalize_input(user_text)
    today_str = get_today_str()
    text = norm.get("clean_text", user_text)

    # 2) 确定性意图路由（不依赖模型）
    action = None

    # reject 路由
    if any(keyword in text for keyword in ["日报", "周报", "总结"]):
        return {
            "ok": True,
            "action": "reject",
            "tool_called": None,
            "today_fragments": [],
            "input_text": user_text
        }

    # confirm 路由
    elif "打卡" in text:
        action = "confirm"
        # 调用 confirm_clock_event
        tool_result = dispatch_tool_call(
            name="confirm_clock_event",
            args={
                "event_type": "start_work",
                "confirmed_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "channel": "manual"
            },
            author=None
        )

        return {
            "ok": True,
            "action": "confirm",
            "tool_called": "confirm_clock_event",
            "today_fragments": [],
            "input_text": user_text
        }

    # query 路由（优先级 3）
    elif any(keyword in text for keyword in ["今天做了啥", "今天干了啥", "今天做了什么", "做了啥", "干了啥", "做了什么"]):
        # author="all" 时传 None，表示不过滤
        query_author = None if author == "all" else author

        print(f"[DEBUG] query: original_author={author}, query_author={query_author}, today={today_str}")

        fragments_result = get_fragments_by_date(
            date=today_str,
            author=query_author
        )

        print(f"[DEBUG] query: returned {fragments_result.get('count', 0)} items")

        return {
            "ok": True,
            "action": "query",
            "tool_called": "get_fragments_by_date",
            "today_fragments": fragments_result.get("items", []),
            "input_text": user_text
        }

    # record 路由（优先级 4，必须满足事实门槛）
    else:
        # 事实门槛：必须包含明确动词
        fact_verbs = ["完成", "执行", "编写", "测试", "修复", "实现", "开发", "部署", "设计"]
        has_fact_verb = any(verb in text for verb in fact_verbs)

        # 事实门槛：非空内容（长度 > 3）且不是纯疑问
        has_content = len(text.strip()) > 3
        is_question = any(marker in text for marker in ["？", "?", "啥", "什么", "吗", "呢"])

        # 判定是否可以 record
        can_record = has_fact_verb and has_content and not is_question

        print(f"[DEBUG] record check: has_fact_verb={has_fact_verb}, has_content={has_content}, is_question={is_question}, can_record={can_record}")

        if can_record:
            # 满足事实门槛，执行 record
            print(f"[DEBUG] record: today_str={today_str}, author={author}")

            # 1) 写入碎片
            record_fragment(
                content=text,
                source="user",
                author=author,
                occurred_date=today_str
            )

            # 2) 立刻查询该作者的今日碎片
            fragments_result = get_fragments_by_date(
                date=today_str,
                author=author
            )

            print(f"[DEBUG] record: returned {fragments_result.get('count', 0)} items")

            return {
                "ok": True,
                "action": "record",
                "tool_called": "record_fragment",
                "today_fragments": fragments_result.get("items", []),
                "input_text": user_text
            }
        else:
            # 不满足事实门槛，当作 query（兜底）
            print(f"[DEBUG] fallback to query: text='{text}', reason='does not meet fact threshold'")

            query_author = None if author == "all" else author
            fragments_result = get_fragments_by_date(
                date=today_str,
                author=query_author
            )

            return {
                "ok": True,
                "action": "query",
                "tool_called": "get_fragments_by_date",
                "today_fragments": fragments_result.get("items", []),
                "input_text": user_text
            }


def main():
    if not API_KEY:
        raise RuntimeError("缺少环境变量 ZHIPU_API_KEY")

    client = ZhipuAI(api_key=API_KEY)

    print("v1.0 已启动（输入 exit 退出）")
    while True:
        try:
            text = input("\n你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出。")
            break

        if not text:
            continue
        if text.lower() in {"exit", "quit"}:
            print("退出。")
            break

        reply = run_once(client, text)
        print(f"系统：{reply}")


if __name__ == "__main__":
    main()
