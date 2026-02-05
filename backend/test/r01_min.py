# r01_min.py
import os
from zhipuai import ZhipuAI
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import tools
tools._FRAGMENTS_PATH_OVERRIDE = "test/fragments_test.jsonl"
from main import run_once_with_structured_response

FRAG_PATH = tools._FRAGMENTS_PATH_OVERRIDE

def count_lines(path):
    if not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)

if __name__ == "__main__":
    author = "一辰a1"
    text = "今天完成 Agent 1.3版本用例执行"

    before = count_lines(FRAG_PATH)

    client = ZhipuAI()

    result = run_once_with_structured_response(
        client=client,
        user_text=text,
        author=author
    )

    after = count_lines(FRAG_PATH)

    print("result:", result)
    print("lines:", before, "->", after)
