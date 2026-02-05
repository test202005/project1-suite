import os
import sys
import json

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from zhipuai import ZhipuAI
from main import run_once_with_structured_response
import tools

# 设置写入路径隔离
TEST_FILE = "test/fragments_test.jsonl"
tools._FRAGMENTS_PATH_OVERRIDE = TEST_FILE

CASES_FILE = "test/cases.jsonl"
ROOT_FRAGMENTS = "fragments.jsonl"


def count_lines(path):
    if not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def main():
    # 清空测试文件
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

    # 读取用例
    cases = []
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    # 初始化 client
    api_key = os.getenv("ZHIPU_API_KEY") or os.getenv("API_KEY", "")
    if not api_key:
        raise RuntimeError("需要设置环境变量 ZHIPU_API_KEY 或 API_KEY")
    client = ZhipuAI(api_key=api_key)

    root_lines_before = count_lines(ROOT_FRAGMENTS)

    print("=" * 60)
    for case in cases:
        before = count_lines(TEST_FILE)
        result = run_once_with_structured_response(
            client=client,
            user_text=case["text"],
            author=case["author"]
        )
        after = count_lines(TEST_FILE)

        action = result.get("action", "")
        lines_changed = after - before
        passed = (action == case["expect_action"] and
                  lines_changed == case["expect_lines_change"])

        status = "PASS" if passed else "FAIL"
        print(f"{case['id']} {case['name']}: action={action}, lines={before}->{after}, {status}")

    root_lines_after = count_lines(ROOT_FRAGMENTS)
    print("=" * 60)
    print(f"Root fragments.jsonl: {root_lines_before}->{root_lines_after} (should not change)")


if __name__ == "__main__":
    main()
