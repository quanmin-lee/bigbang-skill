# Feishu LLM Bot 项目规划

> 飞书机器人：接收用户消息 → 调用 LLM 生成回复 → 支持多轮对话

## 项目概述

在飞书中创建一个智能对话机器人，通过飞书事件订阅接收用户消息，利用 LLM（如 GPT、Claude、通义千问）生成回复，并维护多轮对话上下文，实现连续自然的对话体验。

## 核心能力

| 能力 | 说明 |
|------|------|
| 私聊对话 | 用户与机器人 1v1 对话 |
| 群聊@回复 | 群聊中 @机器人 触发回复 |
| 多轮上下文 | 保留最近 N 轮对话历史 |
| 流式输出 | LLM 逐字输出，用户实时看到回复 |
| 高可用 | WebSocket 长连接 + 自动重连 |

## 架构总览

```
飞书用户 → Feishu WebSocket → Message Receiver → Conversation Manager → LLM Service → Response Sender → 飞书用户
                                   │                      │                    │
                                   │                      ▼                    │
                                   │               Redis / Memory            │
                                   │                 (上下文存储)              │
                                   └──────────────────────────────────────────┘
                                               (所有组件通过日志串联)
```

## 技术栈

- **语言**: Python 3.10+
- **SDK**: lark-oapi（飞书官方 Python SDK）
- **LLM**: OpenAI / Anthropic / 通义千问
- **缓存**: Redis（生产）/ 内存（开发）
- **部署**: systemd + uvicorn / Docker

## 文件清单

| 文件 | 内容 |
|------|------|
| `01-architecture.md` | 系统架构设计（组件、数据流、技术选型） |
| `02-execution-plan.md` | 分阶段执行计划（6 Phase，约 5 人天） |
| `03-prompt-design.md` | Prompt 设计、上下文管理、配置项、边界场景 |

## 快速开始（Phase 0）

```bash
# 1. 创建项目
mkdir feishu-llm-bot && cd feishu-llm-bot
python -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install lark-oapi openai redis loguru pydantic python-dotenv

# 3. 创建飞书应用
#    → 开放平台 → 创建应用 → 启用机器人
#    → 事件订阅 → 添加 im.message.receive_v1
#    → 权限管理 → 开启 im:message 相关权限

# 4. 配置 .env
cp .env.example .env
# 填入 APP_ID, APP_SECRET, API_KEY 等
```

## 补充参考

本项目所处环境的现有 Feishu Agent 项目提供了可复用的实践：

- `feishu_api(operation, params)` 统一 API 封装模式
- `lark_cli(command, args_json)` CLI 包装
- WebSocket 长连接心跳与重连机制
- 事件过滤（自循环消息、群聊@匹配）

但本项目作为一个**独立机器人**，不需要依赖现有项目的复杂 pipeline 架构，保持轻量、专注对话即可。
