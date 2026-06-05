# 飞书 LLM 机器人项目 — 实施计划

## 项目概述

构建一个飞书机器人，接收用户消息、调用 LLM 生成智能回复、支持多轮对话。采用 Python + FastAPI + lark-oapi 技术栈，模块化分层架构。

---

## 一、架构设计

### 整体架构

```
┌──────────────────────────────────────────────────────────┐
│                    FastAPI Server                         │
│                                                            │
│  POST /webhook/event                                       │
│       │                                                    │
│       ▼                                                    │
│  ┌─────────────┐    ┌──────────────────┐                   │
│  │ EventRouter  │───▶│   Handler        │                   │
│  │ (验签/路由)  │    │ (编排主流程)     │                   │
│  └─────────────┘    └───────┬──────────┘                   │
│       ▲                      │                             │
│  (验签失败→403)              │                             │
│                              ▼                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │                Orchestration Flow                 │      │
│  │                                                    │      │
│  │  1. SessionManager.get_context(user_id)            │      │
│  │     → 创建/获取会话上下文                           │      │
│  │  2. LLMService.generate(context + message)          │      │
│  │     → 获取 LLM 回复                                 │      │
│  │  3. MessageSender.send_text(user_id, reply)         │      │
│  │     → 发送回复到飞书                                │      │
│  │  4. SessionManager.add_message(user_id, msg)        │      │
│  │     → 更新对话历史                                  │      │
│  └──────────────────────────────────────────────────┘      │
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │ SessionMgr  │  │ LLMService  │  │ MessageSender   │   │
│  │ (上下文管理) │  │ (API 封装)  │  │ (飞书消息发送)  │   │
│  │ - 内存存储  │  │ - 超时控制  │  │ - Token 管理   │   │
│  │ - TTL 过期  │  │ - 重试机制  │  │ - 自动刷新     │   │
│  │ - 窗口截断  │  │ - 降级策略  │  │ - 限频控制     │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
│                                                            │
│  ┌──────────────────────────────────────────────────┐      │
│  │              ConfigManager                       │      │
│  │  (环境变量/配置文件 → AppID/Secret/Token/APIKey) │      │
│  └──────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────┘
```

### 技术栈

| 层 | 选型 | 说明 |
|----|------|------|
| 运行时 | Python 3.11+ | 异步原生支持 |
| Web 框架 | FastAPI + Uvicorn | 异步高性能，原生支持飞书回调 |
| 飞书 SDK | lark-oapi | 官方 Python SDK，签名验证、消息发送 |
| LLM SDK | OpenAI SDK (兼容接口) | 支持 GPT / Claude 等 |
| 会话存储 | 内存 dict (V1) / Redis (V2) | V1 用内存实现最小主链 |
| 测试 | pytest + pytest-asyncio | 异步测试支持 |
| 部署 | Uvicorn + systemd | 生产级部署 |

### 配置管理

| 配置项 | 来源 | 说明 |
|--------|------|------|
| FEISHU_APP_ID | 环境变量 | 飞书应用 ID |
| FEISHU_APP_SECRET | 环境变量 | 飞书应用 Secret |
| FEISHU_VERIFICATION_TOKEN | 环境变量 | 事件回调验证 Token |
| FEISHU_ENCRYPT_KEY | 环境变量 | 事件回调加密 Key (可选) |
| LLM_API_KEY | 环境变量 | LLM API Key |
| LLM_MODEL | 环境变量 | 模型名称 (默认 gpt-4o-mini) |
| LLM_BASE_URL | 环境变量 | API 端点地址 |
| SESSION_TTL_MINUTES | 环境变量 | 会话过期时间 (默认 30) |
| MAX_HISTORY_ROUNDS | 环境变量 | 最大保留对话轮数 (默认 10) |

---

## 二、执行计划

### Batch 1: [CRITICAL_PATH] 最小主链

| ID | 任务 | 文件 | 类型 | 前置 |
|----|------|------|------|------|
| T1 | 项目初始化 | `pyproject.toml`, `app/__init__.py` | 串行 | 无 |
| T2 | 飞书路由+验签 | `app/config.py`, `app/router.py` | 并行 | T1 |
| T3 | 会话管理器 | `app/session/manager.py`, `app/session/models.py` | 并行 | T1 |
| T4 | LLM 调用服务 | `app/llm/service.py`, `app/llm/prompts.py` | 并行 | T1 |
| T5 | 消息发送服务 | `app/sender.py` (含 Token 管理) | 并行 | T1 |
| T6 | 主流程编排 | `app/handler.py` | 串行 | T2+T3+T4+T5 |
| T7 | E2E 集成 | `app/main.py`, `tests/test_e2e.py` | 串行 | T6 |

**Batch 1 执行顺序**:
```
T1 → 并发(T2, T3, T4, T5) → T6 → T7
```

### Batch 2: [ENHANCEMENT] 功能完善

| ID | 任务 | 文件 | 前置 |
|----|------|------|------|
| T8 | 上下文截断策略 | `app/session/store.py` | T3+T4 |
| T9 | 错误处理与重试 | `app/llm/service.py`, `app/sender.py` | T4+T5 |
| T10 | 日志与监控 | `app/logging.py` | T7 |

---

## 三、接口契约

| 模块 | 输入 | 输出 |
|------|------|------|
| `EventRouter` | HTTP POST (飞书回调, 含签名) | `MessageEvent` 对象 或 HTTP 403 |
| `SessionManager.get_context` | `user_id: str` | `Session` (含消息列表) |
| `SessionManager.add_message` | `user_id: str, message: Message` | `None` |
| `LLMService.generate` | `messages: list[dict]` | `str` 回复文本 |
| `MessageSender.send_text` | `user_id: str, text: str` | `bool` (成功/失败) |
| `Handler.handle_event` | `MessageEvent` | `None` (编排各模块) |

---

## 四、测试策略

### 框架与工具
- **框架**: pytest + pytest-asyncio + pytest-mock
- **Mock**: 飞书 API 和 LLM API 全部 Mock，零外部依赖
- **执行**: 每个 P0 测试独立可运行，不共享会话状态

### P0 测试验收条件

| 任务 | 关键验收条件 |
|------|-------------|
| T1 | 所有模块可导入，目录结构完整 |
| T2 | URL Challenge 返回正确；签名校验通过/拒绝；消息事件正确解析 |
| T3 | 新用户创建会话；已有用户获取历史；多用户隔离；消息可追加 |
| T4 | 正确组装 Prompt；成功返回回复；超时抛异常 |
| T5 | 发送文本消息到正确用户；Token 过期可自动刷新 |
| T6 | 完整编排链路走通：接收→会话→LLM→发送→更新 |
| T7 | E2E 模拟飞书回调，验证 LLM 被调用且发送 API 被调用 |

### 关键测试场景

- **正常路径**: 用户发消息 → LLM 生成 → 回复发送
- **签名错误**: 伪造请求 → HTTP 403
- **LLM 超时**: API 不响应 → 超时异常 → 用户友好提示
- **Token 过期**: 发送时 401 → 自动刷新 → 重试成功
- **并发消息**: 同一用户快速多发消息 → 上下文正确维护
- **会话过期**: 超过 TTL 后发消息 → 创建新会话

---

## 五、风险与缓解

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| 飞书签名验证缺失 | **高** | 强制使用 lark-oapi 内置验签，T2 中作为第一优先级实现 |
| Token 过期未刷新 | **高** | T5 中内置 Token 刷新逻辑，每次 API 调用前检查有效期 |
| LLM API 超时/失败 | **中** | T4 实现超时控制(30s)，T9 实现指数退避重试(3次) |
| 多轮上下文长度失控 | **中** | V1 实现基础窗口截断(保留最近10轮)，V2 升级为摘要压缩 |
| 飞书 API 限频 | **中** | T5 实现请求队列和退避，批量消息时控制发送速率 |
| 内存存储重启丢失 | **低** | V1 明确告知限制，V2 升级 Redis 持久化 |

---

## 六、目录结构

```
feishu-bot/
├── pyproject.toml
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py             # 配置加载（环境变量）
│   ├── router.py             # 飞书事件路由+签名验证
│   ├── handler.py            # 主流程编排
│   ├── sender.py             # 飞书消息发送 (含 Token 管理)
│   ├── session/
│   │   ├── __init__.py
│   │   ├── models.py         # Session/Message 数据模型
│   │   └── manager.py        # 会话管理器 (内存存储)
│   └── llm/
│       ├── __init__.py
│       ├── prompts.py        # System Prompt 模板
│       └── service.py        # LLM API 封装
└── tests/
    ├── __init__.py
    ├── test_router.py        # T2 测试
    ├── test_session.py       # T3 测试
    ├── test_llm.py           # T4 测试
    ├── test_sender.py        # T5 测试
    ├── test_handler.py       # T6 测试
    └── test_e2e.py           # T7 测试
```

---

## 七、实施顺序（TDD）

1. **T1** — 创建目录结构、初始化 pyproject.toml -> RED: 导入测试
2. **并发**:
   - **T2** — 路由+验签 -> RED: 模拟回调 POST 断言 200
   - **T3** — 会话管理 -> RED: 获取新用户上下文断言空列表
   - **T4** — LLM 服务 -> RED: mock 调用断言返回文本
   - **T5** — 消息发送 -> RED: mock 发送断言 API 被调用
3. **T6** — 编排器 -> RED: mock 所有依赖断言完整流程
4. **T7** — E2E -> RED: TestClient 全链路验证
5. **Batch 2**: T8 → T9 → T10 (按序完善)

每个任务严格遵循 RED → GREEN → REFACTOR，GREEN 后立即 `git commit`。
