# server.py
# Flask API 入口：提供 POST /api/input 接口

import os
import sys
import importlib
from flask import Flask, request, jsonify
from zhipuai import ZhipuAI

# 强制重新加载 main 模块（避免缓存）
def reload_main_module():
    """每次请求前重新加载 main 模块"""
    modules_to_clear = ['main', 'tools', 'input_normalizer']
    for mod in modules_to_clear:
        if mod in sys.modules:
            del sys.modules[mod]
    return importlib.import_module('main')

# 首次导入
main_module = reload_main_module()
run_once_with_structured_response = main_module.run_once_with_structured_response

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
        "author": "作者名称",
        "date": "YYYY-MM-DD (可选，默认今天)"
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
    data = None  # Initialize before try block
    try:
        # ✅ 每次请求前重新加载 main 模块
        print("[SERVER] Reloading main module...")
        main_module = reload_main_module()
        run_once_with_structured_response = main_module.run_once_with_structured_response
        print("[SERVER] Module reloaded, function:", run_once_with_structured_response)

        data = request.get_json()

        # 1) author 必填校验
        if not data or 'author' not in data:
            return jsonify({
                "ok": False,
                "error": "missing author field"
            }), 400

        author = data['author']
        text = data.get('text', '')
        target_date = data.get('date')  # 新增：可选的目标日期

        print(f"[SERVER] Processing request: text='{text}', author='{author}', date='{target_date}'")

        # 2) 调用结构化响应函数（传递 target_date）
        result = run_once_with_structured_response(
            client=client,
            user_text=text,
            author=author,
            target_date=target_date  # 新增参数
        )

        print(f"[SERVER] Result: action={result.get('action')}, tool_called={result.get('tool_called')}")

        return jsonify(result)

    except Exception as e:
        import traceback
        print(f"[SERVER] ERROR: {str(e)}")
        print(f"[SERVER] TRACEBACK:\n{traceback.format_exc()}")
        if data:
            print(f"[SERVER] Request: author='{data.get('author', 'N/A')}', text='{data.get('text', 'N/A')}'")
        else:
            print(f"[SERVER] Request: unable to parse JSON")

        return jsonify({
            "ok": False,
            "error": str(e),
            "error_type": type(e).__name__
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok", "version": "v2-fixed"})


@app.route('/api/fragments/<fragment_id>', methods=['DELETE'])
def delete_fragment(fragment_id: str):
    """
    删除指定的 fragment

    Args:
        fragment_id: fragment 的 id

    Returns:
        {"ok": true, "deleted_id": "...", "today_fragments": [...]}
        或 {"ok": false, "error": "..."}
    """
    try:
        from tools import delete_fragment_by_id
        result = delete_fragment_by_id(fragment_id)
        status_code = 200 if result.get("ok") else 404
        return jsonify(result), status_code
    except Exception as e:
        import traceback
        print(f"[SERVER] ERROR in delete_fragment: {str(e)}")
        print(f"[SERVER] TRACEBACK:\n{traceback.format_exc()}")
        return jsonify({
            "ok": False,
            "error": str(e),
            "error_type": type(e).__name__
        }), 500


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
