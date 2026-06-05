# 架构评估报告 — 飞书 LLM 对话机器人

## 需求理解

构建一个飞书机器人，通过飞书 WebSocket 长连接接收用户消息，调用 LLM（如 DeepSeek、GPT 等）生成回复，支持多轮对话。用户在同一会话中可以连续发问，机器人能记住上下文。

核心功能：
1. 飞书消息接收（WebSocket 长连接 / Webhook）
2. 消息解析与路由
3. LLM 调用生成回复
4. 上下文管理（多轮对话）
5. 回复发送（飞书消息 API）
6. 流式输出（可选，提升体验）

## 项目概览

### 参考项目（现有飞书 AI Agent）

本评估参考了同团队已有项目 `Feishu AI Agent` 的架构，该项目的目录结构与关键数据流如下：

```
feishu-ai-agent/
├── src/
│   ├── main.py                 # 入口：组装 Bus → Sender → Dispatcher → Channel
│   ├── config.py               # Settings 类，从 .env 加载配置
│   ├── bus.py                  # MessageBus（异步队列，解耦 inbound/outbound）
│   ├── dispatcher.py           # 消费 inbound，通过 LangGraph agent 处理
│   ├── session.py              # 会话/线程 ID 生成
│   ├── agent/
│   │   ├── agent.py            # LangGraph ReAct Agent 组装
│   │   ├── prompt.py           # 系统 Prompt 构建
│   │   └── context_window.py   # 上下文窗口管理
│   ├── feishu/
│   │   ├── client.py           # lark-oapi 客户端单例
│   │   ├── sender.py           # 消息发送 + running card 生命周期
│   │   └── ws_client.py        # WebSocket 长连接接收消息
│   ├── store/
│   │   ├── memory_store.py     # SQLite 存储（会话、记忆）
│   │   └── checkpointer.py     # LangGraph 检查点
│   └── tools/                  # Agent 工具集
├── skills/                     # 可插拔 Skill
├── data/                       # 运行时数据（DB、缓存）
└── .env                        # 环境变量
```

### 关键数据流

```
用户消息
  │
  ▼
Feishu WS Channel (ws_client.py)
  │  解析消息、去重 → 提取 parse_feishu_event() 独立函数
  ▼
InboundMessage ──MessageBus──► Dispatcher
                                  │
                                  ▼
                           ChatManager (内存对话管理)
                                  │
                                  ▼
                           LLM Client (OpenAI 兼容 API)
                                  │
                                  ▼
                           OutboundMessage ──MessageBus──► Sender
                                                           │
                                                           ▼
                                                    Feishu 消息 API
                                                           │
                                                           ▼
                                                     回复给用户
```

### 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 飞书 SDK | lark-oapi | 官方 Python SDK，支持 WS 长连接 + API 调用 |
| LLM | OpenAI 兼容 API | DeepSeek / GPT / 通义千问 等。V1 支持可配置 endpoint，国内首选 DeepSeek 国内端点 |
| 对话管理 | 内存 dict（V1 简单模式） | 不引入 LangGraph checkpointer，减少外部依赖 |
| 持久化 | 无（V1）；V2 引入 SQLite | 会话记录、用户记忆 |
| 异步 | asyncio + threading | WS 线程桥接到 async loop |
| 测试 | pytest + pytest-asyncio | 全 mock 外部队件 |

## 维度评分

| 维度 | 评分 | 依据 |
|------|------|------|
| 架构健康度 | 4/5 | 消息总线解耦 Inbound/Outbound，组件职责清晰。WS 线程与 async loop 桥接合理。缺点：单通道设计，横向扩展需额外工作。 |
| 可维护性 | 4/5 | 每个文件单职责，函数长度适中，dataclass 定义清晰。消息解析独立为 `parse_feishu_event()` 函数后更易测。 |
| AI 可读性 | 4/5 | 命名自描述（如 `FeishuChannel`、`MessageDispatcher`、`InboundMessage`），类型标注完整。 |
| 模块化 | 4/5 | 各模块通过 MessageBus 接口通信，可独立替换。Feishu 模块与 LLM 模块解耦。 |
| 可测试性 | 3/5 → 4/5 | 消息解析函数可单独测（提升）。但 WS client 集成测试仍需飞书凭证。Mock 策略清晰。 |

## 最小主链（V1） — 精简版

V1 目标：**一个开发日内跑通**。去掉所有非必要依赖，使用最简单的实现。

| 改动点 | 涉及文件 | 风险 | 说明 |
|--------|---------|------|------|
| P1. 项目骨架 + 入口 | `pyproject.toml`, `.env.example`, `src/config.py`, `src/main.py` | 低 | 初始化项目结构 + 配置加载 + 入口函数。合并为一个批次。 |
| P2. 飞书客户端 | `src/feishu/client.py` | 低 | lark-oapi 客户端单例。 |
| P3. 消息解析与消息总线 | `src/feishu/message_parser.py`（新增）, `src/bus.py` | 低 | `parse_feishu_event()` 独立函数用于单元测试。Bus 用 asyncio.Queue。 |
| P4. WebSocket 接收 | `src/feishu/ws_client.py` | 低 | 依赖 P2+P3。WS 线程桥接 + 消息去重。 |
| P5. 消息发送 | `src/feishu/sender.py` | 低 | 回复消息（V1 先做纯文本消息，V2 做交互卡片）。 |
| P6. LLM 客户端 | `src/llm/client.py` | 中 | OpenAI 兼容 API 封装，支持超时重试。国内端点配置。 |
| P7. 内存对话管理 | `src/chat/manager.py` | 中 | `dict[str, list]` 存储消息历史，设置最大轮数（20 轮）。 |
| P8. 分发器 | `src/dispatcher.py` | 中 | 组装主链：消费 inbound → 对话管理 → LLM → outbound。+ 测试 `conftest.py` 和 mock fixtures。 |

## V2+ 建议

- **流式输出**: 飞书交互卡片的 streaming update，提升用户体验
- **用户记忆**: SQLite 存储用户偏好、历史关键词（参考 memory_store.py）
- **LangGraph ReAct Agent**: 工具调用能力（如读取飞书文档）
- **群聊支持**: @机器人识别、群聊多用户上下文隔离
- **管理命令**: `/help`、`/clear`、`/status` 等 slash 命令
- **日志/监控**: 消息量统计、延迟监控、错误告警
- **Webhook 备用**: 如果 WS 连接不稳定，增加 Webhook 回调方式
- **LLM Rate Limit 应对**: 429 响应的指数退避重试策略

## 风险与注意事项

1. **飞书凭证安全**: lark-oapi 需要 app_id / app_secret，必须通过环境变量注入，禁止硬编码
2. **WS 断线重连**: lark-oapi 内置重连机制，但在网络不稳定环境下需验证
3. **LLM 成本**: 多轮对话的上下文累积会增加 token 消耗，20 轮上限是安全保障
4. **并发安全**: 同一个 session 的消息必须串行处理（`_processing_threads` 模式）
5. **异步桥接风险**: `run_coroutine_threadsafe` 在事件循环停止时调用会抛出异常，需加 `is_running()` 检查
6. **国内网络延迟**: 如果使用海外 LLM API 端点，建议增加 `timeout=30s` 并准备国内备选端点（DeepSeek 国内 API: `https://api.deepseek.com/v1` 实际是国内 CDN）
7. **LLM 429 Rate Limit**: 必须实现退避重试，防止被限流后静默丢失请求
