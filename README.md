# Project 1 Suite

这是一个前后端分离的 Demo 项目，用于演示工作记录和打卡功能。

## 项目结构

```
project1-suite/
├── backend/    # 后端服务（Flask + ZhipuAI）
├── frontend/   # 前端页面（React + Vite + TypeScript）
└── docs/       # 测试文档
```

## 快速启动

### 启动后端

```bash
cd backend
pip install -r requirements.txt
python server.py
```

后端服务将运行在 http://localhost:8080

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端页面将运行在 http://localhost:5173（或自动分配的端口）

## 测试

冒烟测试用例见：[docs/testing/smoke-test-iter3.md](docs/testing/smoke-test-iter3.md)

## 技术栈

- **后端**: Flask + ZhipuAI GLM-4.5
- **前端**: React 18 + TypeScript + Vite
- **数据存储**: JSON Lines (JSONL)
