# PLAN — 飞书 LLM 对话机器人

## 概述

构建一个飞书机器人，通过飞书 WebSocket 长连接接收用户消息，调用 LLM（DeepSeek / GPT 等 OpenAI 兼容 API）生成回复，支持多轮对话。

**总体策略**: 
- V1 最小主链在**一个开发日内**跑通端到端消息收发 + LLM 回复 + 多轮对话。
- V2+ 逐步增强流式输出、用户记忆、群聊支持、管理命令。
- 强制 TDD：所有代码必须先写测试再写实现。
- 严格遵循 Git 纪律：增量提交，每个有意义的修改立即 commit。

## 架构决策

### 核心架构

```
用户消息 → WebSocket 接收(独立线程) → parse_feishu_event()
  → InboundMessage → MessageBus(asyncio.Queue) → Dispatcher
  → ChatManager(内存) → LLM Client → OutboundMessage
  → MessageBus → Sender → 飞书消息 API → 回复用户
```

### 关键技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 飞书 SDK | lark-oapi | 官方 Python SDK，WS 长连接 + API |
| LLM | OpenAI 兼容 API | DeepSeek 国内端点优先，可切换 |
| 对话管理 | 内存 dict (V1) | 不引入外部依赖，20 轮上限 |
| 异步 | asyncio + threading | WS 线程桥接到 async loop |
| 测试 | pytest + pytest-asyncio | 全 mock 外部队件 |

### 模块职责

| 模块 | 文件 | 职责 |
|------|------|------|
| Config | `src/config.py` | 环境变量加载、类型转换 |
| Bus | `src/bus.py` | Inbound/Outbound 消息定义 + 异步队列 |
| Feishu Client | `src/feishu/client.py` | lark-oapi 单例 |
| Message Parser | `src/feishu/message_parser.py` | `parse_feishu_event()` 独立函数 |
| WS Channel | `src/feishu/ws_client.py` | WS 线程桥接到 async loop |
| Sender | `src/feishu/sender.py` | 发送消息回复 |
| LLM Client | `src/llm/client.py` | OpenAI 兼容 API 封装，含超时重试 |
| Chat Manager | `src/chat/manager.py` | 内存对话管理，20 轮裁剪 |
| Dispatcher | `src/dispatcher.py` | 编排消息处理流程 |
| Main | `src/main.py` | 组件组装、启动、优雅关闭 |

### 关键设计决策

1. **消息解析独立函数**: `parse_feishu_event()` 从 ws_client 中提取为独立函数，便于单元测试
2. **V1 不做流式卡片**: 普通文字回复，降低发送逻辑复杂度
3. **同 session 串行处理**: `_processing_threads` 集合确保同一 session 的消息不会并发处理
4. **20 轮对话上限**: 避免 token 无限膨胀，超限后自动裁剪最早的消息
5. **LLM 429 退避重试**: HTTP 429 Rate Limit 时指数退避，最多重试 3 次

## 执行计划

### 任务总览

| ID | 任务名 | 类型 | 前置依赖 | 涉及文件 |
|----|--------|------|---------|---------|
| T0 | 测试基础设施 | [CRITICAL_PATH] | 无 | `pyproject.toml`, `tests/conftest.py` |
| T1 | 项目骨架 + 配置 + 入口 | [CRITICAL_PATH] | T0 | `pyproject.toml`, `.env.example`, `src/config.py`, `src/main.py` |
| T2 | 飞书客户端封装 | [CRITICAL_PATH] | T1 | `src/feishu/client.py` |
| T3 | 消息总线 | [CRITICAL_PATH] | T0 | `src/bus.py` |
| T4 | WebSocket 消息接收 | [CRITICAL_PATH] | T1, T2, T3 | `src/feishu/ws_client.py`, `src/feishu/message_parser.py` |
| T5 | 消息发送 | [CRITICAL_PATH] | T1, T2 | `src/feishu/sender.py` |
| T6 | LLM 客户端 | [CRITICAL_PATH] | T1 | `src/llm/client.py` |
| T7 | 内存对话管理 | [CRITICAL_PATH] | T6 | `src/chat/manager.py` |
| T8 | 消息分发器 | [CRITICAL_PATH] | T3, T4, T5, T7 | `src/dispatcher.py` |
| T9 | 入口 main() 集成 | [CRITICAL_PATH] | T8 | `src/main.py`（更新） |
| T10 | 流式输出增强 | [ENHANCEMENT] | T5, T7 | `src/feishu/sender.py`, `src/feishu/card_builder.py` |
| T11 | 用户记忆持久化 | [ENHANCEMENT] | T7 | `src/store/memory.py` |
| T12 | 会话管理命令 | [ENHANCEMENT] | T8 | `src/dispatcher.py` |
| T13 | 日志和 Rate Limit 策略 | [ENHANCEMENT] | T6 | `src/llm/client.py`, `src/logger.py` |

### 批次规划

**Batch 1: [CRITICAL_PATH] 打通主链（按顺序串行）**

```
T0 → T1 → [T2, T3, T6 can be partially parallelised at file level]
  → T4 (depends on T1+T2+T3)
  → T5 (depends on T1+T2)
  → T7 (depends on T6)
  → T8 (depends on T3+T4+T5+T7)
  → T9 (depends on T8)
```

1. T0: `pyproject.toml` 添加 dev deps + `tests/conftest.py`（mock fixtures）
2. T1: 项目结构 + `config.py` + `main.py` 空壳
3. T2: `feishu/client.py` 单例
4. T3: `bus.py` 消息定义 + 队列
5. T4: `message_parser.py` + `ws_client.py`
6. T5: `sender.py`（文字消息）
7. T6: `llm/client.py`（超时重试 + rate limit）
8. T7: `chat/manager.py`（内存 dict + 20 轮裁剪）
9. T8: `dispatcher.py`（组装所有依赖）
10. T9: 更新 `main.py` 组装启动

**Batch 2: [ENHANCEMENT] 功能完善（可并行）**

- T10: 流式交互卡片
- T11: SQLite 记忆持久化
- T12: 管理命令（/help, /clear）
- T13: 日志优化 + Rate Limit 退避策略

### 依赖图

```
T0 ──→ T1 ──┬──→ T2 ──→ T4 ──┐
             │                │
             ├──→ T5 ────────┤
             │               │
             ├──→ T6 ──→ T7 ─┤
             │                │
T3 ─────────────────────────┤
                              │
                              ▼
                             T8 ──→ T9
                                    │
                        ┌───────────┤
                        ▼           ▼
                     T10/T11    T12/T13
```

## 测试策略

### 测试框架与 Mock 策略

- **框架**: pytest + pytest-asyncio
- **全局 Fixtures（`tests/conftest.py`）**:
  - `mock_feishu_client`: mock `lark.Client` 单例
  - `mock_llm`: mock `openai.OpenAI`，返回预设回复
  - `mock_bus`: 创建 `MessageBus` + spy callback
  - `sample_inbound_msg`: `InboundMessage` 工厂函数
- **覆盖率目标**: 核心模块 > 85%

### 按任务 P0 测试重点

| 任务 | P0 测试核心 |
|------|------------|
| T0 | conftest fixture 可被正确注入 |
| T1 | 配置加载正常/异常 |
| T2 | 飞书客户端单例 |
| T3 | inbound/outbound 队列通路 |
| T4 | `parse_feishu_event()` 解析正确；消息去重 |
| T5 | 消息发送 API 调用 |
| T6 | LLM 调用正常 + 超时 + 重试 |
| T7 | 多轮对话上下文保持；session 隔离 |
| T8 | 全部链路集成；同 session 串行 |
| T9 | 组件组装启动 |

### 关键测试场景

1. **多轮对话测试**: 发送 "我叫小明" → 发送 "我叫什么？" → 验证回复含"小明"
2. **Session 隔离**: session A 和 B 同时发消息，上下文互不污染
3. **上下文裁剪**: 超过 20 轮后最早的消息被裁剪，裁剪后对未知问题降级回复
4. **LLM 超时**: mock 30s+ 延迟，验证 `TimeoutError` 抛出
5. **Rate Limit 退避**: mock HTTP 429，验证指数退避重试
6. **消息去重**: 相同 message_id 两次到达，第二次被跳过
7. **同 session 串行**: 同一 chat 快速发 2 条消息，顺序处理不乱序

### 测试执行顺序

```
Batch 1 测试:
  T3(bus) → T1(config) → T2(client) → T6(LLM) → T7(session)
  → T4(parser) → T5(sender) → T8(dispatcher) → T9(main)

Batch 2 测试:
  T10 / T11 / T12 / T13 可独立并行测试
```

### 注意事项

- 所有 LLM 调用测试必须 mock，避免真实 token 消耗
- 集成测试标注 `@pytest.mark.integration`，需要真实飞书凭证
- 测试间不能共享 session 状态
- 使用 `pytest-asyncio` 处理异步协程测试

## 附录

### 项目目录结构

```
feishu-llm-bot/
├── pyproject.toml          # 项目配置 + 依赖
├── .env.example            # 环境变量模板
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── config.py           # Settings 类
│   ├── bus.py              # 消息总线
│   ├── dispatcher.py       # 消息分发器
│   ├── main.py             # 入口 + 组件组装
│   ├── feishu/
│   │   ├── __init__.py
│   │   ├── client.py       # lark-oapi 单例
│   │   ├── message_parser.py # parse_feishu_event()
│   │   ├── ws_client.py    # WS 线程桥接
│   │   └── sender.py       # 消息发送
│   ├── llm/
│   │   ├── __init__.py
│   │   └── client.py       # OpenAI 兼容 API 封装
│   └── chat/
│       ├── __init__.py
│       └── manager.py      # 内存对话管理
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # 全局 mock fixtures
│   ├── test_bus.py
│   ├── test_config.py
│   ├── test_dispatcher.py
│   ├── test_feishu_client.py
│   ├── test_llm_client.py
│   ├── test_message_parser.py
│   ├── test_chat_manager.py
│   └── test_sender.py
└── data/                   # 运行时数据（V2 引入）
```

### 环境变量 (.env.example)

```
# 飞书应用配置
FEISHU_APP_ID=cli_xxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxx

# LLM API 配置（OpenAI 兼容）
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 运行时
MAX_CONCURRENCY=5
LOG_LEVEL=INFO
```

### 风险与注意事项

1. **飞书凭证安全**: 必须通过环境变量注入，禁止硬编码
2. **WS 断线重连**: lark-oapi 内置重连，需验证稳定性
3. **LLM Token 成本**: 20 轮对话上限 + 裁剪策略是安全保障
4. **并发安全**: 同 session 串行，不同 session 并行
5. **国内网络**: 优先使用国内 LLM 端点（DeepSeek），设置 30s 超时
6. **Rate Limit**: HTTP 429 必须指数退避重试
7. **TDD 纪律**: 所有代码必须先写测试，RED → GREEN → REFACTOR
8. **增量提交**: 每完成一个任务立即 `git commit`，禁止累积
