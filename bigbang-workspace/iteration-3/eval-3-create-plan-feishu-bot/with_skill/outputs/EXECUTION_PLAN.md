# 执行计划

## 任务总览

| ID | 任务名 | 类型 | 前置依赖 | 涉及文件 |
|----|--------|------|---------|---------|
| T1 | 项目骨架初始化 | [CRITICAL_PATH] | 无 | pyproject.toml, .env.example, main.py, src/__init__.py |
| T2 | 配置管理模块 | [CRITICAL_PATH] | T1 | src/config.py |
| T3 | 会话存储实现 | [CRITICAL_PATH] | T1 | src/session/store.py |
| T4 | 会话管理器实现 | [CRITICAL_PATH] | T3 | src/session/manager.py |
| T5 | LLM 客户端封装 | [CRITICAL_PATH] | T1 | src/llm/client.py, src/llm/prompts.py |
| T6 | 飞书 WebSocket 连接 + 事件监听 | [CRITICAL_PATH] | T1, T2 | src/bot.py |
| T7 | 消息处理编排 | [CRITICAL_PATH] | T4, T5, T6 | src/handler/message.py |
| T8 | 入口文件整合 | [CRITICAL_PATH] | T2, T7 | main.py |
| T9 | 端到端集成测试 | [ENHANCEMENT] | T8 | tests/test_e2e.py |
| T10 | 单元测试 | [ENHANCEMENT] | T8 | tests/test_*.py |

## 批次规划

### Batch 1: [CRITICAL_PATH] 打通主链 (串行)

```
T1 → T2 → [T3, T5] → T4 → T6 → T7 → T8
```

各任务说明：

- **T1: 项目骨架初始化**
  - 创建目录结构、pyproject.toml、main.py 桩文件
  - 安装依赖：lark-oapi, openai/anthropic, pydantic-settings

- **T2: 配置管理模块**
  - 基于 Pydantic Settings 读取飞书凭证、LLM API Key 等
  - 提供类型安全的全局配置对象

- **T3: 会话存储实现** [parallel]
  - 实现 `SessionStore` 抽象基类 + `SqliteSessionStore` 具体实现
  - 支持 create / append / get_history / trim 操作

- **T5: LLM 客户端封装** [parallel]
  - 实现 `LlmClient` 封装 API 调用
  - 支持 system prompt + message history 拼接
  - 注意：T3 和 T5 无数据依赖，可并发

- **T4: 会话管理器实现**
  - 依赖 T3：在 store 之上封装会话逻辑
  - 按 session_id 路由、历史截断策略、超时清理

- **T6: 飞书 WebSocket 连接**
  - 使用 lark-oapi 建立 WS 长连接
  - 注册 `im.message.receive_v1` 事件处理器
  - 实现断线自动重连

- **T7: 消息处理编排**
  - 依赖 T4 + T5 + T6：串联"收到消息 → 查会话 → 调 LLM → 存对话 → 回复"
  - 是核心编排逻辑

- **T8: 入口文件整合**
  - 在 main.py 中组装所有模块
  - 启动 uvicorn 异步服务

### Batch 2: [ENHANCEMENT] 测试完善

- T9: 端到端集成测试（模拟飞书消息 → 验证 LLM 回复流程）
- T10: 单元测试（session / llm / handler 各模块）

## 依赖图

```
T1 (骨架) ───→ T2 (配置)
                  │
                  ├──→ T3 (会话存储) ──→ T4 (会话管理器) ──┐
                  │                                         │
                  └──→ T5 (LLM客户端) ──────────────────────┤
                                                            │
T6 (飞书WS) ───────────────────────────────────────────────┤
                                                           │
                                              T7 (消息编排) ←┘
                                                           │
                                              T8 (入口整合) ←┘
```

## 风险与注意事项

- **T3 与 T5 的并发**：T3 写 `session/store.py`，T5 写 `llm/client.py`，完全独立文件，可安全并发
- **T6 WebSocket 重连**：需确认 lark-oapi 是否内置重连，若没有需手动实现指数退避
- **T7 编排边界**：消息 handler 不应包含 LLM 或 session 的具体实现逻辑，只做编排
- **飞书事件结构**：需提前了解 `im.message.receive_v1` 的事件体字段结构
