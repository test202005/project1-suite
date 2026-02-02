#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for date picker functionality"""

import requests
import json
import sys

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, 'strict')

BASE_URL = "http://localhost:8080"

def api_request(method, endpoint, data=None):
    """Unified API request"""
    url = f"{BASE_URL}{endpoint}"
    if method == "POST":
        response = requests.post(url, json=data)
    elif method == "DELETE":
        response = requests.delete(url)
    else:
        raise ValueError(f"Unknown method: {method}")

    try:
        return response.json()
    except:
        return {"ok": False, "error": "Invalid JSON response", "status": response.status_code}

print("=" * 70)
print("Test 1: Create fragment for yesterday (2025-02-02)")
print("=" * 70)
result = api_request("POST", "/api/input", {
    "text": "完成昨天的工作任务",
    "author": "test_user",
    "date": "2025-02-02"
})
print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

print("\n" + "=" * 70)
print("Test 2: Create fragment for today (default behavior)")
print("=" * 70)
result = api_request("POST", "/api/input", {
    "text": "完成今天的工作任务",
    "author": "test_user"
})
print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

print("\n" + "=" * 70)
print("Test 3: Query yesterday's fragments")
print("=" * 70)
result = api_request("POST", "/api/input", {
    "text": "今天做了啥",
    "author": "test_user",
    "date": "2025-02-02"
})
print(f"Found {len(result.get('today_fragments', []))} fragments for 2025-02-02")
for frag in result.get('today_fragments', []):
    print(f"  - {frag.get('content')} (date: {frag.get('occurred_date')})")

print("\n" + "=" * 70)
print("Test 4: Query today's fragments (should be different)")
print("=" * 70)
result = api_request("POST", "/api/input", {
    "text": "今天做了啥",
    "author": "test_user",
})
fragments = result.get('today_fragments', [])
print(f"Found {len(fragments)} fragments for today")
for frag in fragments:
    print(f"  - {frag.get('content')} (date: {frag.get('occurred_date')})")

print("\n" + "=" * 70)
print("Test 5: Clock-in for yesterday")
print("=" * 70)
result = api_request("POST", "/api/input", {
    "text": "帮我打卡",
    "author": "test_user_clock",
    "date": "2025-02-02"
})
print(f"Response action: {result.get('action')}")
fragments = result.get('today_fragments', [])
if fragments:
    print(f"Clock-in fragment created:")
    print(f"  Content: {fragments[0].get('content')}")
    print(f"  Date: {fragments[0].get('occurred_date')}")

print("\n" + "=" * 70)
print("Test 6: Summary for yesterday")
print("=" * 70)
# First create some work fragments for yesterday
api_request("POST", "/api/input", {
    "text": "完成WMS用例执行",
    "author": "test_user_summary",
    "date": "2025-02-02"
})
api_request("POST", "/api/input", {
    "text": "完成接口开发",
    "author": "test_user_summary",
    "date": "2025-02-02"
})
# Then create summary
result = api_request("POST", "/api/input", {
    "text": "总结今日",
    "author": "test_user_summary",
    "date": "2025-02-02"
})
print(f"Response action: {result.get('action')}")
fragments = result.get('today_fragments', [])
summary = [f for f in fragments if f.get('type') == 'summary']
if summary:
    print(f"Summary created for date: {summary[0].get('occurred_date')}")
    print(f"Summary preview: {summary[0].get('content')[:100]}...")

print("\n" + "=" * 70)
print("All tests completed!")
print("=" * 70)
