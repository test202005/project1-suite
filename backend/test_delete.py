#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for delete functionality"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_create_fragment():
    """创建测试碎片"""
    response = requests.post(
        f"{BASE_URL}/api/input",
        json={"text": "完成删除功能测试", "author": "testuser"}
    )
    print(f"Create fragment response: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    return response.json()

def test_query_fragments(author):
    """查询碎片"""
    response = requests.post(
        f"{BASE_URL}/api/input",
        json={"text": "今天做了啥", "author": author}
    )
    print(f"\nQuery fragments response: {response.status_code}")
    result = response.json()
    fragments = result.get("today_fragments", [])
    print(f"Found {len(fragments)} fragments")
    for frag in fragments:
        print(f"  - ID: {frag.get('id', 'NO ID')}, Content: {frag.get('content')}")
    return fragments

def test_delete_fragment(fragment_id):
    """删除碎片"""
    print(f"\nDeleting fragment: {fragment_id}")
    response = requests.delete(f"{BASE_URL}/api/fragments/{fragment_id}")
    print(f"Delete response: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    return response.json()

if __name__ == "__main__":
    print("=" * 60)
    print("Test 1: Create a fragment with ID")
    print("=" * 60)
    create_result = test_create_fragment()

    print("\n" + "=" * 60)
    print("Test 2: Query fragments to get ID")
    print("=" * 60)
    fragments = test_query_fragments("testuser")

    if fragments:
        # Get the first fragment with an ID
        target = None
        for frag in fragments:
            if frag.get("id"):
                target = frag
                break

        if target:
            fragment_id = target["id"]
            print(f"\nFound fragment with ID: {fragment_id}")
            print(f"Content: {target['content']}")

            print("\n" + "=" * 60)
            print("Test 3: Delete the fragment")
            print("=" * 60)
            delete_result = test_delete_fragment(fragment_id)

            print("\n" + "=" * 60)
            print("Test 4: Query again to verify deletion")
            print("=" * 60)
            fragments_after = test_query_fragments("testuser")

            remaining_ids = [f.get("id") for f in fragments_after if f.get("id")]
            if fragment_id not in remaining_ids:
                print(f"\n✓ SUCCESS: Fragment {fragment_id} was deleted")
            else:
                print(f"\n✗ FAILURE: Fragment {fragment_id} still exists")
        else:
            print("\n⚠ WARNING: No fragments with ID found")
    else:
        print("\n⚠ WARNING: No fragments found for testuser")
