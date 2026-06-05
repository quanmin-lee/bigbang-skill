# 执行计划 — 飞书 LLM 对话机器人

## 任务总览

| ID | 任务名 | 类型 | 前置依赖 | 涉及文件 |
|----|--------|------|---------|---------|
| T0 | 测试基础设施 | [CRITICAL_PATH] | 无 | `pyproject.toml` (dev deps), `tests/conftest.py`, `tests/` 目录 |
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

## 批次规划

### Batch 1: [CRITICAL_PATH] 打通主链

```
T0 (测试基础设施)
  │
  ├── T1 (项目骨架+配置) ──→ T4 (WS 接收)
  │       │                    │
  │       ├── T2 (飞书客户端) ──┘
  │       │
  │       ├── T5 (消息发送)
  │       │
  │       └── T6 (LLM 客户端) ──→ T7 (对话管理)
  │
  └── T3 (消息总线) ──────────→ T8 (分发器)
                                  │
                                  └── T9 (入口集成)
```

#### 批次内执行顺序

1. **T0** [串行] 测试基础设施
   - 添加 pytest / pytest-asyncio 到 dev dependencies
   - 创建 `tests/` 目录和 `tests/conftest.py`（全局 fixtures：mock feishu client、mock LLM、mock bus）
   - 创建 `tests/__init__.py`

2. **T1** [串行] 项目骨架 + 配置 + 入口框架
   - `pyproject.toml` 配置运行时依赖（lark-oapi, openai）
   - `.env.example` 模板
   - `src/config.py` Settings 类
   - `src/main.py` 空白入口结构

3. **T2** [串行] 飞书客户端（依赖 T1）
   - 封装 lark-oapi Client 单例
   - 从配置读取 app_id / app_secret

4. **T3** [串行] 消息总线（可独立于 T1 测试）
   - `InboundMessage` / `OutboundMessage` dataclass
   - `MessageBus` with asyncio.Queue

5. **T4** [串行] WebSocket 接收（依赖 T1, T2, T3）
   - `src/feishu/message_parser.py` — `parse_feishu_event()` 独立函数，可单测
   - `src/feishu/ws_client.py` — WS 线程桥接

6. **T5** [串行] 消息发送（依赖 T1, T2）
   - 发送文字消息（V1 阶段不做流式卡片）

7. **T6** [串行] LLM 客户端（依赖 T1）
   - OpenAI 兼容 API 封装
   - 超时设置（30s）+ 重试策略（最多 2 次，含 429 rate limit 退避）

8. **T7** [串行] 对话管理（依赖 T6）
   - 内存 `dict[str, list]` 存储
   - 20 轮上下文上限 + 自动裁剪

9. **T8** [串行] 消息分发器（依赖 T3, T4, T5, T7）
   - 消费 inbound → 调用对话管理 → 发送 outbound
   - 同 session 串行保护（`_processing_threads`）

10. **T9** [串行] 入口 main() 集成
    - 组装所有组件
    - 启动 async loop + 优雅关闭

### Batch 2: [ENHANCEMENT] 功能完善

这批任务依赖 Batch 1 完成后的主链，任务间无强依赖，可并行：

```
T10 ──┐
T11 ──┤  (可并行)
T12 ──┤
T13 ──┘
```

1. **T10** [并行] 流式输出增强
   - 飞书交互卡片的 streaming update
   - Card builder 工具函数

2. **T11** [并行] 用户记忆持久化
   - SQLite 存储用户历史记忆
   - 启动时加载，对话中更新

3. **T12** [并行] 会话管理命令
   - `/help`, `/clear`, `/memory` 等
   - 路由逻辑注入 dispatcher

4. **T13** [并行] 日志和错误处理 + Rate Limit 策略
   - structured logging 配置
   - Rate Limit 指数退避

## 依赖图

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

## 风险与注意事项

1. **T0 不能跳过**: TDD 强制要求，测试基础设施必须先于任何代码任务
2. **T6 依赖 T1 配置**: LLM 客户端需要 API key 和 endpoint 配置
3. **T7 简化策略**: V1 用内存存储对话历史，不引入 LangGraph checkpointer 或数据库
4. **T8 并发保护**: 同 session 必须串行；不同 session 可以并行
5. **国内网络**: LLM API 端点需配置国内可用的 CDN 或镜像地址
