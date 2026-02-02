# server.py
# Flask API 入口：提供 POST /api/input 接口

import os
import sys
import importlib
from flask import Flask, request, jsonify
from zhipuai import ZhipuAI

# 强制重新加载 main 模块（避免缓存）
if 'main' in sys.modules:
    del sys.modules['main']
if 'tools' in sys.modules:
    del sys.modules['tools']
if 'input_normalizer' in sys.modules:
    del sys.modules['input_normalizer']

from main import run_once_with_structured_response

app = Flask(__name__)

# 环境变量
MODEL_NAME = os.getenv("ZHIPU_MODEL", "glm-4.5")
API_KEY = os.getenv("ZHIPU_API_KEY", "")

if not API_KEY:
    raise RuntimeError("缺少环境变量 ZHIPU_API_KEY")

# 初始化智谱客户端
client = ZhipuAI(api_key=API_KEY)


@app.route('/api/input', methods=['POST'])
def api_input():
    """
    统一输入接口

    请求体：
    {
        "text": "用户输入文本",
        "author": "作者名称"
    }

    响应体：
    {
        "ok": true,
        "action": "record" | "query" | "confirm" | "reject",
        "tool_called": "record_fragment" | "get_fragments_by_date" | ... | null,
        "today_fragments": [...],
        "input_text": "原始输入"
    }
    """
    data = request.get_json()

    # 1) author 必填校验
    if not data or 'author' not in data:
        return jsonify({
            "ok": False,
            "error": "missing author field"
        }), 400

    author = data['author']
    text = data.get('text', '')

    # 2) 调用结构化响应函数
    result = run_once_with_structured_response(
        client=client,
        user_text=text,
        author=author
    )

    return jsonify(result)


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok", "version": "v2-fixed"})


@app.route('/debug', methods=['GET'])
def debug():
    """调试端点：检查代码是���被加载"""
    text = "做了啥"
    keywords = ["今天做了啥", "今天干了啥", "今天做了什么", "做了啥", "干了啥", "做了什么"]
    match = any(keyword in text for keyword in keywords)
    return jsonify({
        "text": text,
        "keywords": keywords,
        "match": match,
        "matched_keywords": [k for k in keywords if k in text]
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"启动服务器：http://localhost:{port}")
    print(f"API 端点：POST http://localhost:{port}/api/input")
    app.run(host='0.0.0.0', port=port, debug=False)
