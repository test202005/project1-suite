# tools.py
# v1.0 Tools JSON Schema + 最小本地实现（文件存储）
#
# 数据文件：
# - fragments.jsonl: 每行一条事实碎片
# - clock.json: 当天打卡状态（按 date 存）

from __future__ import annotations

import json
import os
from datetime import datetime, date
from typing import Any, Dict, List, Optional


DATA_DIR = os.getenv("DATA_DIR", ".")
FRAGMENTS_PATH = os.path.join(DATA_DIR, "fragments.jsonl")
CLOCK_PATH = os.path.join(DATA_DIR, "clock.json")


# =========================
# 1) Function Calling Schemas（严格对齐你的判定表）
# =========================

function_schemas: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "record_fragment",
            "description": (
                "记录一条“未经加工的事实碎片”（append-only）。"
                "仅用于清晰、可复用的工作事实陈述；不用于情绪/吐槽/评价/混合句。"
                "occurred_date 为可选参数；若用户未提供日期或语义为“今天/现在”，必须直接使用今天日期（YYYY-MM-DD）调用 record_fragment，不要向用户追问日期。"
            ),
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "content": {"type": "string", "minLength": 1, "maxLength": 400},
                    "occurred_date": {
                        "type": "string",
                        "pattern": r"^\d{4}-\d{2}-\d{2}$",
                        "description": "YYYY-MM-DD",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1, "maxLength": 20},
                        "maxItems": 5,
                    },
                    "source": {"type": "string", "enum": ["user"]},
                    "author": {"type": "string", "minLength": 1, "maxLength": 50},
                },
                "required": ["content", "source", "author"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fragments_by_date",
            "description": "查询指定日期的所有事实碎片（只读）。用于“回顾/梳理”前置取数，不生成日报。",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 200},
                    "order": {"type": "string", "enum": ["asc", "desc"], "default": "asc"},
                    "author": {"type": "string", "description": "按作者过滤；不传则不过滤"},
                },
                "required": ["date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_clock_event",
            "description": "记录一次打卡确认（人→系统）。用于明确确认语义，不做合法性判断。",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "event_type": {"type": "string", "enum": ["start_work", "end_work"]},
                    "confirmed_at": {
                        "type": "string",
                        "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$",
                    },
                    "channel": {"type": "string", "enum": ["manual"]},
                    "note": {"type": "string", "maxLength": 200},
                },
                "required": ["event_type", "confirmed_at", "channel"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mark_clock_timeout",
            "description": "记录一次打卡超时事实（系统→事实）。只记录，不补救。",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "event_type": {"type": "string", "enum": ["start_work", "end_work"]},
                    "deadline_at": {
                        "type": "string",
                        "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$",
                    },
                    "timeout_at": {
                        "type": "string",
                        "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$",
                    },
                    "reason": {"type": "string", "enum": ["no_confirmation"]},
                },
                "required": ["event_type", "deadline_at", "timeout_at", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_clock_status",
            "description": "查询当前打卡状态（只读）。用于回答“我打卡了吗”等状态查询。"
            "date 为可选参数；当用户询问“今天打卡了吗 / 查询打卡状态”等当前日期相关问题且未提供 date 时，必须默认使用今天日期（YYYY-MM-DD）调用工具，不要向用户追问日期。",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                    "event_type": {
                        "type": "string",
                        "enum": ["start_work", "end_work", "all"],
                        "default": "all",
                    },
                },
                "required": [],
            },
        },
    },
]


# =========================
# 2) Minimal storage helpers
# =========================

def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _load_clock() -> Dict[str, Any]:
    _ensure_data_dir()
    if not os.path.exists(CLOCK_PATH):
        return {}
    try:
        with open(CLOCK_PATH, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def _save_clock(clock: Dict[str, Any]) -> None:
    _ensure_data_dir()
    with open(CLOCK_PATH, "w", encoding="utf-8") as f:
        json.dump(clock, f, ensure_ascii=False, indent=2)


def _append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    _ensure_data_dir()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


# =========================
# 3) Tool implementations
# =========================

def record_fragment(content: str, source: str, author: str, occurred_date: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    if not occurred_date:
        occurred_date = date.today().strftime("%Y-%m-%d")
    item = {
        "type": "fragment",
        "content": content.strip(),
        "occurred_date": occurred_date,
        "source": source,
        "author": author,
        "tags": tags or [],
        "created_at": _now_iso(),
    }
    _append_jsonl(FRAGMENTS_PATH, item)
    return {"ok": True, "saved": item}


def get_fragments_by_date(date: str, limit: int = 200, order: str = "asc", author: Optional[str] = None) -> Dict[str, Any]:
    rows = [r for r in _read_jsonl(FRAGMENTS_PATH) if r.get("occurred_date") == date]

    # 按 author 过滤（如果提供了有效的 author）
    # author=None 或 author="" 都表示不过滤，返回所有人的记录
    if author is not None and author != "":
        rows = [r for r in rows if r.get("author") == author]

    if order == "desc":
        rows = list(reversed(rows))
    rows = rows[: max(1, min(int(limit), 200))]

    # 调试日志
    print(f"[DEBUG] get_fragments_by_date: date={date}, author_filter={author}, returned_count={len(rows)}")

    return {"ok": True, "date": date, "count": len(rows), "items": rows}


def confirm_clock_event(event_type: str, confirmed_at: str, channel: str, note: str = "") -> Dict[str, Any]:
    clock = _load_clock()
    d = confirmed_at.split("T", 1)[0]
    clock.setdefault(d, {})
    clock[d][event_type] = {
        "status": "confirmed",
        "confirmed_at": confirmed_at,
        "channel": channel,
        "note": note,
        "updated_at": _now_iso(),
    }
    _save_clock(clock)
    return {"ok": True, "date": d, "event_type": event_type, "state": clock[d][event_type]}


def mark_clock_timeout(event_type: str, deadline_at: str, timeout_at: str, reason: str) -> Dict[str, Any]:
    clock = _load_clock()
    d = deadline_at.split("T", 1)[0]
    clock.setdefault(d, {})
    # 若已确认，不覆盖（从严：超时事实可以记录，但不篡改“已确认”）
    existing = clock[d].get(event_type)
    if existing and existing.get("status") == "confirmed":
        return {"ok": True, "skipped": True, "reason": "already_confirmed", "existing": existing}

    clock[d][event_type] = {
        "status": "timeout",
        "deadline_at": deadline_at,
        "timeout_at": timeout_at,
        "reason": reason,
        "updated_at": _now_iso(),
    }
    _save_clock(clock)
    return {"ok": True, "date": d, "event_type": event_type, "state": clock[d][event_type]}


def get_clock_status(date: str | None = None, event_type: str = "all") -> Dict[str, Any]:
    clock = _load_clock()
    day = clock.get(date, {})
    if event_type == "all":
        return {"ok": True, "date": date, "items": day}
    return {"ok": True, "date": date, "event_type": event_type, "item": day.get(event_type)}


# =========================
# 4) Dispatcher
# =========================

_ALLOWED_TOOLS = {
    "record_fragment": record_fragment,
    "get_fragments_by_date": get_fragments_by_date,
    "confirm_clock_event": confirm_clock_event,
    "mark_clock_timeout": mark_clock_timeout,
    "get_clock_status": get_clock_status,
}


def dispatch_tool_call(name: Optional[str], args: Dict[str, Any], author: Optional[str] = None) -> Dict[str, Any]:
    if not name or name not in _ALLOWED_TOOLS:
        return {"ok": False, "error": "tool_not_allowed", "name": name}

    fn = _ALLOWED_TOOLS[name]

    # 为工具注入 author 参数
    if name in ["record_fragment", "get_fragments_by_date"] and author is not None:
        if "author" not in args:
            args["author"] = author

    # 补默认 date/datetime
    if name == "record_fragment" and "occurred_date" not in args:
        args.setdefault("occurred_date", None)
    elif name == "get_fragments_by_date" and "date" not in args:
        args.setdefault("date", date.today().strftime("%Y-%m-%d"))
    elif name == "get_clock_status" and "date" not in args:
        args.setdefault("date", date.today().strftime("%Y-%m-%d"))
    elif name == "confirm_clock_event" and "confirmed_at" not in args:
        args.setdefault("confirmed_at", datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
    try:
        return fn(**args)  # type: ignore[arg-type]
    except TypeError as e:
        return {"ok": False, "error": "bad_arguments", "name": name, "detail": str(e), "args": args}
    except Exception as e:
        return {"ok": False, "error": "tool_failed", "name": name, "detail": str(e)}
