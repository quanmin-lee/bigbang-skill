# Feishu LLM Bot -- 系统架构

## 概述

飞书机器人项目，通过飞书 WebSocket 长连接接收用户私聊/群聊消息，调用 LLM 生成回复，支持多轮对话上下文。

---

## 整体架构

```
User (Feishu)  ←→  Feishu API Gateway
                        │
                   [WebSocket / Webhook]
                        │
              ┌─────────▼──────────┐
              │   Message Receiver  │  ← lark-oapi EventDispatcher
              │   (事件/回调入口)     │
              └─────────┬──────────┘
                        │
              ┌─────────▼──────────┐
              │  Conversation Mgr   │  ← 多轮对话上下文管理
              │  (Context / Memory) │
              └─────────┬──────────┘
                        │
              ┌─────────▼──────────┐
              │   LLM Service       │  ← OpenAI / Claude / 通义千问
              │   (模型调用 + 流式)   │
              └─────────┬──────────┘
                        │
              ┌─────────▼──────────┐
              │   Response Sender   │  ← 飞信消息发送 API
              │   (回复消息)         │
              └────────────────────┘
```

## 核心组件

### 1. Message Receiver (消息接收层)

- 使用 `lark-oapi` SDK 建立 WebSocket 长连接（推荐）或 Webhook
- 注册 `im.message.receive_v1` 事件
- 区分私聊 (`chat_type = "p2p"`) 与群聊 (`chat_type = "group"`)
- 过滤机器人自己的消息，避免自循环
- 异常重连机制

### 2. Conversation Manager (对话管理)

- **上下文存储**：Redis (推荐) / SQLite / 内存
- 每个 `sender_id + chat_id` 为一个对话 session
- 滑动窗口策略：保留最近 N 轮 (user + assistant) 作为 LLM 上下文
- TTL 过期策略：会话超过 30 分钟无活动自动清理
- 支持 system prompt 注入（角色设定、知识库上下文）

### 3. LLM Service (模型调用)

- 统一的 LLM 接口抽象，支持多 provider：
  - OpenAI / Azure OpenAI
  - Anthropic Claude
  - 通义千问 (DashScope)
  - 本地部署模型 (vLLM / Ollama)
- 支持流式输出 (`stream=True`) 实时推送给用户
- 可配置的 max_tokens、temperature、top_p 等参数
- Prompt 模板系统：支持按场景使用不同 prompt

### 4. Response Sender (回复发送)

- 使用 Feishu `send_message` API 回传消息
- 支持纯文本、富文本、消息卡片 (interactive card) 等多种消息类型
- 流式场景：先发送占位消息，逐步 append 内容
- 错误处理：LLM 超时/失败时回复兜底文案

---

## 数据流

```
1. 用户发送消息 → Feishu 服务器 → WebSocket 推送
2. Message Receiver 收到事件，解析 sender_id, chat_id, message content
3. Conversation Manager 根据 (chat_id, sender_id) 加载历史上下文
4. LLM Service 组装 messages = [system_prompt, ...history, user_message]
5. LLM 返回回复文本（同步或流式）
6. Response Sender 调用 Feishu API 发送消息给用户
7. 将本次 {(user_message, assistant_reply)} 存入上下文
8. 更新会话 TTL
```

---

## 技术栈建议

| 层次 | 技术选型 |
|------|----------|
| SDK | `lark-oapi` (Python) |
| 运行环境 | Python 3.10+ / FastAPI (可选，如果不用 WebSocket) |
| 对话缓存 | Redis (生产) / 内存 dict (开发) |
| LLM | OpenAI / Claude / 通义千问 API |
| 部署 | systemd + uvicorn / Docker |
| 日志 | loguru |
