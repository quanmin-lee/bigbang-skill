# 架构评估报告

## 需求理解

构建一个飞书机器人项目，核心功能：
1. 通过飞书 WebSocket 长连接接收用户消息
2. 调用 LLM（大语言模型）生成回复
3. 支持多轮对话（维护对话上下文）

## 项目概览

### 技术栈建议

| 层 | 技术选型 | 说明 |
|---|---------|------|
| 机器人框架 | lark-oapi (飞书官方 Python SDK) | 官方维护，支持 WebSocket 事件订阅 |
| LLM SDK | openai / anthropic SDK | 兼容主流 LLM API |
| 会话存储 | SQLite + dict cache | 轻量持久化 + 内存加速 |
| 部署 | uvicorn 异步服务 | 与 lark-oapi 的异步事件循环兼容 |
| 配置管理 | Pydantic Settings | 环境变量 + .env 文件 |

### 主要目录结构（建议）

```
feishu-bot/
├── main.py                  # 入口：启动事件监听
├── pyproject.toml           # 项目依赖
├── .env.example             # 环境变量模板
├── src/
│   ├── __init__.py
│   ├── config.py            # 配置管理
│   ├── bot.py               # 飞书机器人事件处理
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py        # LLM API 封装
│   │   └── prompts.py       # 系统提示词
│   ├── session/
│   │   ├── __init__.py
│   │   ├── manager.py       # 会话管理器
│   │   └── store.py         # 会话存储抽象
│   └── handler/
│       ├── __init__.py
│       ├── message.py       # 消息处理路由
│       └── middleware.py    # 中间件（日志、限流等）
└── tests/
    ├── conftest.py
    ├── test_session.py
    ├── test_llm_client.py
    └── test_message_handler.py
```

### 关键数据流

```
飞书 WebSocket (长连接)
    │
    ▼
lark-oapi 事件分发
    │
    ▼
message_handler.on_message(event)
    │
    ├── 1. 提取: user_id, chat_id, text, msg_id
    │
    ├── 2. session_manager.get_or_create(session_id)
    │       └── 加载对话历史 (最多 N 轮)
    │
    ├── 3. llm_client.generate(history + new_msg)
    │       └── 调用 LLM API → 返回回复文本
    │
    ├── 4. session_manager.append(session_id, user_msg, bot_reply)
    │       └── 更新持久化存储
    │
    └── 5. bot.reply_message(chat_id, reply_text)
```

## 维度评分

| 维度 | 评分 | 依据 |
|------|------|------|
| 架构健康度 | 4/5 | 关注点清晰分离：事件接收 / 会话管理 / LLM 调用 / 回复发送，各层职责明确 |
| 可维护性 | 4/5 | 模块化设计，每个模块有单一职责；配置集中管理 |
| AI 可读性 | 5/5 | 命名自描述，目录结构简单清晰，函数职责单一 |
| 模块化 | 4/5 | session / llm / handler 三层解耦；可单独替换 LLM 实现或存储后端 |
| 可测试性 | 4/5 | LLM client 和 session store 均可 mock；消息处理可独立测试；需注意 lark-oapi 事件模拟 |

## 最小主链（V1）

| 改动点 | 涉及文件 | 风险 | 说明 |
|--------|---------|------|------|
| 项目骨架 + 配置 | pyproject.toml, main.py, config.py | 低 | 标准 Python 项目初始化 |
| 飞书 WebSocket 连接 | main.py, bot.py | 中 | 需正确配置飞书 App ID/Secret；网络连通性依赖 |
| LLM 客户端封装 | llm/client.py, llm/prompts.py | 低 | 标准 API 调用，可 mock |
| 会话管理器 | session/manager.py, session/store.py | 中 | 需处理多用户并发写、历史截断策略 |
| 消息处理路由 | handler/message.py | 低 | 核心编排逻辑，将前 4 步串联 |
| 端到端集成测试 | tests/test_e2e.py | 低 | 验证真实数据流 |

## V2+ 建议

- 限流和频率控制（防止 LLM API 超预算）
- 流式回复（SSE / 逐字输出）
- 富文本回复（飞书消息卡片）
- 多 LLM Provider 切换
- Sentry / 日志监控
- Agent / Tool-use 能力

## 风险与注意事项

- **飞书凭证安全**：App ID / Secret 不要硬编码，使用环境变量
- **历史窗口管理**：多轮对话需要设定截断策略（如保留最近 10 轮），否则 token 开销线性增长
- **LLM 延迟**：LLM API 响应时间 1-5s，需要合理设置超时
- **WebSocket 重连**：飞书长连接可能断开，需要实现自动重连机制
- **并发安全**：多用户同时发消息时，会话存储的读写需要线程安全
