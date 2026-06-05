# 测试验收边界

## 测试策略

| 项目 | 选择 | 说明 |
|------|------|------|
| 测试框架 | pytest | Python 生态标准，内置 fixture 和参数化 |
| Mock | pytest-mock (mocker fixture) | 对 LLM API、飞书 API、文件 IO 进行 mock |
| 存储测试 | SQLite 内存模式 (`:memory:`) | 避免测试污染文件系统 |
| 异步支持 | pytest-asyncio | 整个项目基于 asyncio，测试需支持 async |
| 覆盖率目标 | V1 ≥ 90%，整体 ≥ 80% | 主链必须高覆盖 |

## 按任务分解

### T1: 项目骨架初始化 (非功能性，无测试)

### T2: 配置管理模块 (P0)

- **验收条件**:
  - 从环境变量读取飞书 App ID / Secret / LLM API Key
  - 未设置时抛出明确的配置错误
  - 支持 `.env` 文件加载
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常加载 | 设置全部环境变量 | Config 对象字段正确 | P0 |
| 缺少飞书 App ID | 未设置 FEISHU_APP_ID | ConfigError 异常 | P0 |
| 缺少 LLM API Key | 未设置 LLM_API_KEY | ConfigError 异常 | P0 |
| .env 文件加载 | 存在 .env 文件且变量正确 | Config 对象正确 | P1 |

- **RED 测试**: `test_config_missing_required_field` — 不设置必要环境变量，期望抛出 `ConfigError`
- **GREEN 最小实现**: 用 Pydantic `Field(validation_alias=...)` + `model_config` 实现环境变量映射

### T3: 会话存储 (P0)

- **验收条件**:
  - 支持创建新会话并返回 session_id
  - 支持追加用户消息和机器人回复
  - 支持按 session_id 获取历史记录
  - 支持截断历史（保留最近 N 轮）
  - 并发写不丢数据
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 创建并追加 | create + append(user_msg) + append(bot_reply) | 历史包含 2 条消息 | P0 |
| 获取历史 | 追加 3 轮对话后 get_history(id) | 返回 6 条消息 (按时间排序) | P0 |
| 截断策略 | 追加 15 轮，max_rounds=10 | 只返回最近 10 轮 (20 条) | P1 |
| 不存在的 session | get_history("nonexistent") | 返回空列表 | P0 |
| 并发追加 | 两个 coroutine 同时 append | 数据不丢失，顺序正确 | P1 |

- **RED 测试**: `test_session_store_create_and_append` — 创建 session 后追加消息，验证历史中存在该消息
- **GREEN 最小实现**: SQLite `:memory:` + `json.dumps` 存储消息列表

### T4: 会话管理器 (P0)

- **验收条件**:
  - `get_or_create(session_id)` 返回会话对象
  - `append(session_id, user_msg, bot_reply)` 自动调用 store
  - 支持 `clear_expired(days=N)` 清理过期会话
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 获取已有会话 | 先创建再 get_or_create | 返回同一会话 (含历史) | P0 |
| 获取新会话 | get_or_create("new_id") | 返回空历史的新会话 | P0 |
| 追加消息 | append + get_history | 含用户和机器人消息 | P0 |
| 过期清理 | 创建旧会话后 clear_expired | 旧会话被清理 | P1 |

- **RED 测试**: `test_session_manager_get_or_create_returns_same_session`
- **GREEN 最小实现**: 包装 T3 的 SessionStore，加过期时间戳

### T5: LLM 客户端 (P0)

- **验收条件**:
  - 调用 `generate(messages)` 返回文本回复
  - 支持自定义 system prompt
  - API 失败时抛出明确的异常
  - 支持超时设置
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常调用 | 发送用户消息 | 返回非空字符串 | P0 |
| 携带 system prompt | system + user messages | 回复遵循 system prompt 风格 | P0 |
| API 超时 | 超时设置为 0.001s | LlmTimeoutError | P1 |
| API 返回错误 | mock 返回 4xx/5xx | LlmApiError | P1 |
| 空消息 | 发送空字符串 | 按照 LLM 行为处理 | P2 |

- **RED 测试**: `test_llm_client_generate_returns_string` — mock LLM API 响应，验证返回 str 类型且非空
- **GREEN 最小实现**: 用 httpx 或 openai SDK 调用 API，返回 `response.choices[0].message.content`

### T6: 飞书 WebSocket 连接 (P0)

- **验收条件**:
  - 连接建立后注册事件处理器
  - 收到 `im.message.receive_v1` 事件时触发回调
  - 断线后自动重连
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 连接成功 | 正确配置启动 | 事件监听器注册成功 | P0 |
| 事件分发 | 收到模拟消息事件 | 回调函数被调用 | P1 |
| 断线重连 | WebSocket 断开 | 自动重连 (mock 验证重连逻辑) | P1 |

- **RED 测试**: `test_bot_register_event_handler` — 初始化 bot 后验证事件处理已注册
- **GREEN 最小实现**: lark-oapi `ws.Client` 的 `start()` 方法

### T7: 消息处理编排 (P0)

- **验收条件**:
  - 收到消息后调用 session 管理器
  - 调用 LLM 客户端
  - 将 LLM 回复发送回飞书
  - 完整链路不走飞书时可 mock 验证
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常消息 | 用户发送 "你好" | 调用 LLM 并回复 | P0 |
| 空消息 | 用户发送空文本 | 不调用 LLM 或返回提示 | P1 |
| 长消息截断 | 超长文本 (超过 max_tokens) | 截断后发送给 LLM | P2 |
| 异常回退 | LLM 调用失败 | 返回友好错误提示 | P1 |

- **RED 测试**: `test_message_handler_full_flow` — mock session/llm/bot 三层，验证编排顺序正确
- **GREEN 最小实现**: handler 编排函数调用 T4.get_or_create → T5.generate → T4.append → bot.reply

### T8: 入口整合 (P0)

- **验收条件**:
  - main.py 能正常启动
  - 所有模块正确组装
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 启动验证 | import main | 无导入错误 | P0 |

- **RED 测试**: `test_main_imports` — `from main import ...` 不报错
- **GREEN 最小实现**: 在 main.py 中实例化所有模块并调用 bot.start()

### T9: 端到端集成测试 (P1)

- **验收条件**:
  - 模拟飞书消息事件
  - 验证完整链条：事件 → 会话 → LLM → 回复
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 完整链路 | 模拟 im.message.receive_v1 | 最终 bot.reply_message 被调用 | P1 |
| 多轮对话 | 同一 session 发 3 条消息 | 每次回复后历史增长 | P1 |

### T10: 单元测试补充 (P2)

- session: 并发竞争、SQLite 错误恢复
- llm: 重试逻辑、速率限制
- handler: 多用户并发、特殊字符处理

## 测试执行顺序

```
Batch 1 (可并发):
  test_config.py          [T2]
  test_session_store.py   [T3]
  test_llm_client.py      [T5]

Batch 2 (依赖 Batch 1):
  test_session_manager.py [T4]

Batch 3 (依赖 Batch 2):
  test_bot.py             [T6]
  test_message_handler.py [T7]

Batch 4:
  test_main.py            [T8]
  test_e2e.py             [T9]
```

## 注意事项

- 所有 LLM API 调用测试必须 mock，不产生真实 API 费用
- SQLite `:memory:` 模式每个测试函数独立创建，不共享状态
- 异步测试需要 `pytest-asyncio` 和 `@pytest.mark.asyncio`
- 飞书事件结构参考 lark-oapi 的 `im.message.receive_v1` 类型定义
