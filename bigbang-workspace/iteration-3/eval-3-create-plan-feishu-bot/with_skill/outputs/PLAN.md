# 飞书机器人项目 Plan

## 项目概述

构建一个飞书机器人，通过 WebSocket 长连接接收用户消息，调用 LLM 生成回复，支持多轮对话上下文。

**技术栈**: Python + lark-oapi + openai/anthropic SDK + Pydantic Settings + SQLite + pytest

---

## 架构决策

### 1. 三层解耦架构

```
飞书 WebSocket (lark-oapi)
       │
       ▼
┌─────────────────────┐
│  handler/message.py │  编排层：路由、组合
│     (编排层)        │
└──────┬──────────┬───┘
       │          │
       ▼          ▼
┌──────────┐ ┌──────────┐
│ session/ │ │ llm/     │  逻辑层：各自独立
│ manager  │ │ client   │
│ + store  │ │ + prompts│
└──────────┘ └──────────┘
```

### 2. 关键数据流

```
用户消息 → 飞书 WS → bot.event_handler → message_handler.handle()
  → session.get_or_create(session_id)    # 获取/创建会话
    → session.get_history()              # 加载历史上下文
  → llm.generate(system_prompt + history + new_msg)
    → session.append(user_msg, reply)    # 持久化对话
  → bot.reply_message(chat_id, reply)    # 发送回复
```

### 3. 配置管理

使用 Pydantic Settings 从环境变量 / `.env` 文件加载：

| 变量 | 说明 |
|------|------|
| `FEISHU_APP_ID` | 飞书应用 App ID |
| `FEISHU_APP_SECRET` | 飞书应用 Secret |
| `LLM_API_KEY` | LLM API 密钥 |
| `LLM_API_BASE` | LLM API 地址（可选） |
| `LLM_MODEL` | 模型名称（可选，默认 gpt-4o-mini） |
| `SESSION_MAX_ROUNDS` | 多轮对话最大轮数（可选，默认 10） |

### 4. 会话存储策略

- **持久层**: SQLite（`sessions.db`）
- **数据结构**: `{session_id, messages: [{"role", "content", "timestamp"}, ...], created_at, updated_at}`
- **截断策略**: 保留最近 N 轮对话（默认 10 轮），由 `SESSION_MAX_ROUNDS` 配置
- **过期清理**: 超过 7 天无活跃的会话自动清理（后台定时任务）

### 5. 消息去重（幂等性）

飞书可能重复推送同一 `msg_id`，handler 层维护已处理 `msg_id` 集合（LRU 缓存，上限 1000），重复消息直接丢弃。

---

## 执行计划

### 目录结构

```
feishu-bot/
├── main.py
├── pyproject.toml
├── .env.example
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── bot.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── prompts.py
│   ├── session/
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   └── store.py
│   └── handler/
│       ├── __init__.py
│       └── message.py
└── tests/
    ├── conftest.py
    ├── test_config.py
    ├── test_session_store.py
    ├── test_session_manager.py
    ├── test_llm_client.py
    ├── test_bot.py
    ├── test_message_handler.py
    ├── test_main.py
    └── test_e2e.py
```

### Batch 1: [CRITICAL_PATH] 最小主链

| # | 任务 | 文件 | 前置 |
|---|------|------|------|
| T1 | 项目骨架 + pyproject.toml + .env.example + 空目录 | 多个 | 无 |
| T2 | 配置管理 Pydantic Settings | src/config.py | T1 |
| T3 | SQLite 会话存储 | src/session/store.py | T1 |
| T4 | LLM 客户端 (可 mock 的 API 封装) | src/llm/client.py, prompts.py | T1 |
| T5 | 会话管理器 (get_or_create / append / trim) | src/session/manager.py | T3 |
| T6 | 飞书 WS 连接 + 事件注册 | src/bot.py | T1 + T2 |
| T7 | 消息编排 handler (串联 session + llm + bot) | src/handler/message.py | T5 + T4 + T6 |
| T8 | main.py 入口整合 | main.py | T2 + T7 |

**并发策略**: T3（session store）和 T4（LLM client）完全独立文件，可安全并行开发。

### Batch 2: [ENHANCEMENT] 测试完善

| # | 任务 | 说明 | 前置 |
|---|------|------|------|
| T9 | 单元测试 | config / session / llm / handler 各模块 | T8 |
| T10 | 端到端集成测试 | mock 飞书事件 → 验证全链路 | T8 |

---

## 测试策略

### 框架与工具

- **pytest** + **pytest-asyncio** + **pytest-mock**
- SQLite `:memory:` 模式确保测试间完全隔离
- 所有 LLM API 调用全部 mock，不产生真实调用费用

### P0 核心测试（必须通过）

| 模块 | 测试要点 |
|------|---------|
| config | 缺少必要环境变量时抛出 ConfigError |
| session/store | 创建 / 追加 / 读取 / 不存在的 session 返回空列表 |
| session/manager | get_or_create 返回同一会话 / append 正确持久化 |
| llm/client | generate 返回非空字符串 / 携带 system prompt |
| message/handler | 完整编排顺序：session → llm → 回复发送 |
| main | 模块导入无错误 |

### P1 增强测试

- 会话历史截断（超过 max_rounds 自动裁剪）
- LLM API 超时和错误回退
- 断线重连逻辑
- 多轮对话完整性验证
- 并发追加不丢数据

---

## 输入/输出契约

| 组件 | 输入 | 输出 |
|------|------|------|
| Config | 环境变量 / .env | 类型安全的配置对象 |
| SessionStore | session_id + messages | 持久化 / 查询消息列表 |
| SessionManager | session_id + 消息 | 会话对象（含历史） |
| LlmClient | messages + system prompt | 回复文本字符串 |
| MessageHandler | 飞书 im.message.receive_v1 事件 | 调用 bot.reply_message |
| Bot | 飞书 WebSocket 事件 | 事件分发到 handler |

---

## 关键风险与前置条件

### 前置条件（开发前确认）

1. **飞书开发者后台已创建应用**，获取 App ID 和 App Secret
2. **已配置事件订阅**：`im.message.receive_v1` 事件已启用
3. **已开通权限**：`im:message` 相关权限已添加并发布版本
4. **LLM API 密钥已准备**：OpenAI / Anthropic / 其他兼容 API

### 风险项

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| WebSocket 断连 | 中 | 确认 lark-oapi 重连机制，若无则手动实现指数退避 |
| LLM API 延迟 | 中 | 设置合理超时（默认 30s），异常时返回友好提示 |
| LLM 费用超支 | 中 | 测试阶段全部 mock；生产环境加日/月预算限制 |
| 消息重复投递 | 低 | handler 层实现 msg_id 去重 |
| 多用户并发写冲突 | 低 | SQLite 的 WAL 模式 + asyncio lock |

### V2+ 规划（本次不实现）

- 流式回复（逐字输出到飞书消息）
- 飞书富文本消息卡片
- 多 LLM Provider 自动切换
- 用户限流（防止刷接口）
- Tool-use / function calling
- 日志监控（Sentry）
