#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Smoke tests for delete functionality (ASCII output)"""

import requests
import json
import time
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

def get_fragments_with_id(author):
    """Get all fragments (must have ID) for author"""
    result = api_request("POST", "/api/input", {"text": "今天做了啥", "author": author})
    fragments = result.get("today_fragments", [])
    return [f for f in fragments if f.get("id")]

def find_clock_in_fragment(author):
    """Find clock-in record"""
    result = api_request("POST", "/api/input", {"text": "今天做了啥", "author": author})
    fragments = result.get("today_fragments", [])
    for f in fragments:
        if "打卡" in f.get("content", "") and f.get("id"):
            return f
    return None

def find_summary_fragment(author):
    """Find summary record"""
    result = api_request("POST", "/api/input", {"text": "今天做了啥", "author": author})
    fragments = result.get("today_fragments", [])
    for f in fragments:
        if f.get("type") == "summary" and f.get("id"):
            return f
    return None

print("=" * 70)
print("Smoke Tests - Delete Fragment Feature")
print("=" * 70)

TEST_AUTHOR = "smoke_test_user"

# Cleanup old test records
print("\n[Cleanup] Deleting old test records...")
old_fragments = get_fragments_with_id(TEST_AUTHOR)
for frag in old_fragments:
    api_request("DELETE", f"/api/fragments/{frag['id']}")
print(f"[Cleanup] Deleted {len(old_fragments)} old records")

test_results = []

# Test Case 1: Delete normal fragment
print("\n" + "=" * 70)
print("Test 1: Delete normal fragment")
print("=" * 70)
print("[Step 1] Creating normal work fragment...")
create_result = api_request("POST", "/api/input", {
    "text": "完成冒烟测试用例1",
    "author": TEST_AUTHOR
})
if not create_result.get("ok"):
    print(f"[FAIL] Create failed: {create_result}")
    test_results.append(("Test 1", False, "Create failed"))
else:
    fragments = get_fragments_with_id(TEST_AUTHOR)
    if not fragments:
        print("[FAIL] Cannot find fragment after creation")
        test_results.append(("Test 1", False, "Not found after create"))
    else:
        target_id = fragments[0]["id"]
        print(f"[OK] Created successfully, ID: {target_id}")
        print(f"[Step 2] Deleting fragment...")
        delete_result = api_request("DELETE", f"/api/fragments/{target_id}")
        if not delete_result.get("ok"):
            print(f"[FAIL] Delete failed: {delete_result}")
            test_results.append(("Test 1", False, "Delete API failed"))
        else:
            print(f"[OK] Delete API returned success")
            print(f"[Step 3] Verifying deletion...")
            fragments_after = get_fragments_with_id(TEST_AUTHOR)
            if target_id in [f.get("id") for f in fragments_after]:
                print("[FAIL] Fragment still exists after deletion")
                test_results.append(("Test 1", False, "Still exists after delete"))
            else:
                print("[OK] Fragment disappeared immediately")
                print(f"[Step 4] Simulating refresh (re-query)...")
                time.sleep(0.5)
                fragments_refresh = get_fragments_with_id(TEST_AUTHOR)
                if target_id in [f.get("id") for f in fragments_refresh]:
                    print("[FAIL] Fragment reappeared after refresh")
                    test_results.append(("Test 1", False, "Reappeared after refresh"))
                else:
                    print("[OK] F5 refresh does not bring it back")
                    test_results.append(("Test 1", True, ""))

# Test Case 2: Delete summary
print("\n" + "=" * 70)
print("Test 2: Delete summary")
print("=" * 70)
print("[Step 1] Creating work fragments first...")
api_request("POST", "/api/input", {"text": "完成工作A", "author": TEST_AUTHOR})
api_request("POST", "/api/input", {"text": "完成工作B", "author": TEST_AUTHOR})
print("[Step 2] Creating summary...")
create_result = api_request("POST", "/api/input", {
    "text": "总结今日",
    "author": TEST_AUTHOR
})
if not create_result.get("ok"):
    print(f"[FAIL] Summary failed: {create_result}")
    test_results.append(("Test 2", False, "Summary create failed"))
else:
    summary_frag = find_summary_fragment(TEST_AUTHOR)
    if not summary_frag:
        print("[FAIL] Cannot find summary after creation")
        test_results.append(("Test 2", False, "Summary not found"))
    else:
        summary_id = summary_frag["id"]
        print(f"[OK] Summary created successfully, ID: {summary_id}")
        print(f"[Step 3] Deleting summary...")
        delete_result = api_request("DELETE", f"/api/fragments/{summary_id}")
        if not delete_result.get("ok"):
            print(f"[FAIL] Delete failed: {delete_result}")
            test_results.append(("Test 2", False, "Delete API failed"))
        else:
            print("[OK] Delete API returned success")
            print(f"[Step 4] Verifying summary disappeared...")
            summary_after = find_summary_fragment(TEST_AUTHOR)
            if summary_after and summary_after.get("id") == summary_id:
                print("[FAIL] Summary still exists after deletion")
                test_results.append(("Test 2", False, "Still exists after delete"))
            else:
                print("[OK] Summary card disappeared")
                print(f"[Step 5] Simulating refresh...")
                time.sleep(0.5)
                summary_refresh = find_summary_fragment(TEST_AUTHOR)
                if summary_refresh and summary_refresh.get("id") == summary_id:
                    print("[FAIL] Summary reappeared after refresh")
                    test_results.append(("Test 2", False, "Reappeared after refresh"))
                else:
                    print("[OK] Refresh still does not show it")
                    test_results.append(("Test 2", True, ""))

# Test Case 3: Delete clock-in record
print("\n" + "=" * 70)
print("Test 3: Delete clock-in record")
print("=" * 70)
print("[Step 1] Creating clock-in record...")
create_result = api_request("POST", "/api/input", {
    "text": "帮我打卡",
    "author": TEST_AUTHOR
})
if not create_result.get("ok"):
    print(f"[FAIL] Clock-in failed: {create_result}")
    test_results.append(("Test 3", False, "Clock-in failed"))
else:
    clock_frag = find_clock_in_fragment(TEST_AUTHOR)
    if not clock_frag:
        print("[FAIL] Cannot find clock-in record")
        test_results.append(("Test 3", False, "Clock-in not found"))
    else:
        clock_id = clock_frag["id"]
        print(f"[OK] Clock-in created successfully, ID: {clock_id}")
        print(f"[Step 2] Deleting clock-in record...")
        delete_result = api_request("DELETE", f"/api/fragments/{clock_id}")
        if not delete_result.get("ok"):
            print(f"[FAIL] Delete failed: {delete_result}")
            test_results.append(("Test 3", False, "Delete API failed"))
        else:
            print("[OK] Delete API returned success")
            print(f"[Step 3] Verifying clock status changed...")
            clock_after = find_clock_in_fragment(TEST_AUTHOR)
            if clock_after and clock_after.get("id") == clock_id:
                print("[FAIL] Clock-in record still exists")
                test_results.append(("Test 3", False, "Still exists after delete"))
            else:
                print("[OK] Header status changed to 'not clocked in'")
                print(f"[Step 4] Simulating refresh...")
                time.sleep(0.5)
                clock_refresh = find_clock_in_fragment(TEST_AUTHOR)
                if clock_refresh and clock_refresh.get("id") == clock_id:
                    print("[FAIL] Clock-in reappeared after refresh")
                    test_results.append(("Test 3", False, "Reappeared after refresh"))
                else:
                    print("[OK] Refresh still shows 'not clocked in'")
                    test_results.append(("Test 3", True, ""))

# Test Case 4: Delete non-existent ID
print("\n" + "=" * 70)
print("Test 4: Delete non-existent ID")
print("=" * 70)
fake_id = "00000000000000000000000000000000"
print(f"[Step 1] Deleting non-existent ID: {fake_id}...")
delete_result = api_request("DELETE", f"/api/fragments/{fake_id}")
if delete_result.get("ok"):
    print("[FAIL] Should not return success")
    test_results.append(("Test 4", False, "Should return error"))
elif "error" in delete_result:
    print(f"[OK] Correctly returned error: {delete_result.get('error')}")
    test_results.append(("Test 4", True, ""))
else:
    print(f"[FAIL] Unexpected response: {delete_result}")
    test_results.append(("Test 4", False, "Unexpected response"))

# Summary
print("\n" + "=" * 70)
print("Test Results Summary")
print("=" * 70)
pass_count = sum(1 for _, passed, _ in test_results if passed)
total_count = len(test_results)

for test_name, passed, error in test_results:
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {test_name}")
    if error:
        print(f"       Error: {error}")

print("\n" + "=" * 70)
print(f"Total: {pass_count}/{total_count} passed")
if pass_count == total_count:
    print("All smoke tests passed - Ready to commit")
else:
    print("Some tests failed - Please fix and retry")
print("=" * 70)
