# 迭代二最终版 API 测试脚本
# 使用方法：
# 1. 启动服务器：python server.py
# 2. 在另一个终端运行此脚本：bash test_api.sh（或逐条执行 curl 命令）

BASE_URL="http://localhost:8080"

echo "=== 测试用例 1：author 缺失 → 400 ==="
curl -X POST $BASE_URL/api/input \
  -H "Content-Type: application/json" \
  -d '{"text": "今天完成了WMS用例执行"}' \
  -w "\nHTTP Status: %{http_code}\n\n"

echo "=== 测试用例 2：记录碎片 → action=record ==="
curl -X POST $BASE_URL/api/input \
  -H "Content-Type: application/json" \
  -d '{"text": "今天完成了WMS用例执行", "author": "张三"}' \
  -w "\nHTTP Status: %{http_code}\n\n"

echo "=== 测试用例 3：按 author 过滤查询（李四） ==="
curl -X POST $BASE_URL/api/input \
  -H "Content-Type: application/json" \
  -d '{"text": "今天做了啥", "author": "李四"}' \
  -w "\nHTTP Status: %{http_code}\n\n"

echo "=== 测试用例 4：author=all 查询全组 ==="
curl -X POST $BASE_URL/api/input \
  -H "Content-Type: application/json" \
  -d '{"text": "今天做了啥", "author": "all"}' \
  -w "\nHTTP Status: %{http_code}\n\n"

echo "=== 测试用例 5：reject 场景 ==="
curl -X POST $BASE_URL/api/input \
  -H "Content-Type: application/json" \
  -d '{"text": "你好", "author": "张三"}' \
  -w "\nHTTP Status: %{http_code}\n\n"

echo "=== 测试用例 6：confirm 场景 ==="
curl -X POST $BASE_URL/api/input \
  -H "Content-Type: application/json" \
  -d '{"text": "帮我打卡", "author": "张三"}' \
  -w "\nHTTP Status: %{http_code}\n\n"

echo "=== 健康检查 ==="
curl -X GET $BASE_URL/health
echo ""
