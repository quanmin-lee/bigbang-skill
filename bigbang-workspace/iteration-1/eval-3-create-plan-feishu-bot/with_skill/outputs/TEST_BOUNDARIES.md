# 测试验收边界 — 飞书 LLM 对话机器人

## 测试策略

- **测试框架**: pytest + pytest-asyncio
- **Mock 策略**:
  - 飞书 API: `unittest.mock.patch` 拦截 `lark_oapi` 客户端调用（fixtures 在 `tests/conftest.py` 中全局定义）
  - LLM API: mock `openai.OpenAI` SDK 调用（conftest 中定义 `mock_llm` fixture）
  - WS 消息: 直接调用 `parse_feishu_event()` 注入测试数据
- **测试级别**: 单元测试为主（可脱离飞书环境运行），集成测试标注 `@pytest.mark.integration`
- **覆盖率目标**: 核心模块（bus, dispatcher, llm client, session）> 85%

## 全局 Fixtures（conftest.py）

```
mock_feishu_client  →  mock lark.Client singleton
mock_llm            →  mock openai.Client, 返回固定回复
mock_bus            →  创建 MessageBus 并附加 spy callback
sample_inbound_msg  →  标准 InboundMessage 工厂
```

## 按任务分解

### T0: 测试基础设施 (P0)

- **验收条件**:
  - `pytest` 可运行，发现 `tests/` 目录下的测试
  - `tests/conftest.py` 提供全局 mock fixtures
  - 所有 fixture 可被测试函数正确注入
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| pytest 发现测试 | `pytest tests/ --collect-only` | 测试函数被收集到 | P0 |
| mock_feishu_client | 注入测试函数 | 返回 mock 对象，不发起真实 HTTP 请求 | P0 |
| mock_llm fixture | 注入测试函数 | LLM 调用返回预设回复 | P0 |

### T1: 项目骨架 + 配置 + 入口 (P0)

- **验收条件**:
  - 项目结构创建完成
  - 配置从 `.env` 正确加载，缺失必填字段抛出明确错误
  - `src/main.py` 可被 Python 导入
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常路径 | 完整 `.env` | `settings.FEISHU_APP_ID` 等字段非空 | P0 |
| 缺失必填字段 | 空 `.env` | 抛出 `ValueError`，指明缺失字段名 | P0 |
| 类型转换 | `MAX_CONCURRENCY=3` | `int` 类型，值为 3 | P1 |

- **RED 测试**: 测试 `config.py` 加载后 `FEISHU_APP_ID` 不为空
- **GREEN 最小实现**: `Settings` 类从 `os.getenv()` 读取

### T2: 飞书客户端封装 (P0)

- **验收条件**:
  - `get_client()` 返回 `lark.Client` 实例
  - 多次调用返回同一实例（单例）
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常初始化 | 调用 `get_client()` | 返回 `lark.Client` 实例 | P0 |
| 单例缓存 | 连续调用两次 | `is` 判断为同一对象 | P0 |
| 配置缺失 | FEISHU_APP_ID 为空 | 返回客户端但后续 API 调用会失败 | P1 |

- **RED 测试**: `mock.patch` 注入 app_id/app_secret，验证 `lark.Client.builder()` 被调用
- **GREEN 最小实现**: 参照 `client.py` 现有实现

### T3: 消息总线 (P0)

- **验收条件**:
  - `InboundMessage` / `OutboundMessage` dataclass 定义完整
  - `MessageBus` 的 inbound 队列可 put/get
  - outbound 回调注册和触发
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| inbound 入列出列 | `InboundMessage` | 出列的是同一个对象 | P0 |
| outbound 回调触发 | `OutboundMessage` | 回调函数被调用，参数正确 | P0 |
| 无回调注册 | publish_outbound | 日志警告，不抛出异常 | P1 |
| 并发 put/get | 多协程同时操作 | 无数据竞争，消息完整 | P1 |

- **RED 测试**: 创建 bus，put inbound，assert get_inbound 返回同一对象
- **GREEN 最小实现**: `asyncio.Queue` + 回调属性

### T4: WebSocket 消息接收 (P0)

- **验收条件**:
  - `parse_feishu_event()` 独立函数可正确解析飞书消息事件
  - WS 线程启动后注册 `im.message.receive_v1` 事件
  - 文字消息解析后转为 `InboundMessage`
  - 非文字消息（图片、文件等）被忽略
  - 重复消息去重
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 文字消息（parse 函数） | standard text event dict | 返回 `InboundMessage` | P0 |
| 群聊消息 | `chat_type=group` | `chat_type="group"` | P0 |
| 非文字消息 | 图片消息 event | 返回 `None` | P0 |
| 重复消息 ID | 相同 message_id | 第二次调用 `process_message` 跳过 | P0 |
| 空 content | 空 JSON | 记录日志，返回 `None` | P1 |
| 富文本消息 | 含 text/img 混排 | 提取 text 部分，[image] 占位 | P1 |

- **RED 测试**: 直接调用 `parse_feishu_event(mock_event_data)`，验证返回的 `InboundMessage` 字段
- **GREEN 最小实现**: `parse_feishu_event()` 处理飞书事件数据，提取关键字段

### T5: 消息发送 (P0)

- **验收条件**:
  - 能发送文字消息到指定 chat_id
  - 能回复 thread 内的消息
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 发送文字消息 | chat_id + text | 调用飞书 API `message.create` | P0 |
| 回复消息 | source_message_id | 调用 `message.reply` | P0 |
| 发送失败 | API 返回错误 | 记录错误日志，不崩溃 | P1 |

- **RED 测试**: mock 飞书客户端，验证 `im.v1.message.create` 被调用
- **GREEN 最小实现**: `asyncio.to_thread` 包装飞书 API 调用

### T6: LLM 客户端 (P0)

- **验收条件**:
  - 调用 OpenAI 兼容 API 生成回复
  - 支持自定义 system prompt
  - 超时处理（30s）
  - 错误重试（最多 2 次）
  - Rate Limit（HTTP 429）指数退避重试
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常生成 | 用户消息 | 返回字符串回复 | P0 |
| 带 system prompt | system + user 消息 | system prompt 被正确设置 | P0 |
| API 超时 | 模拟 30s+ 延迟 | 抛出 `TimeoutError` | P0 |
| HTTP 500 临时错误 | 首次 500，次次 200 | 重试后成功返回 | P1 |
| HTTP 429 Rate Limit | 连续 429 | 指数退避，最多重试 3 次 | P1 |
| 连续错误 | 全部失败 | 抛出 `RuntimeError` | P1 |
| 国内端点配置 | endpoint 设为 DeepSeek 国内 URL | 请求发往正确端点 | P1 |

- **RED 测试**: mock `openai.OpenAI`，验证 `chat.completions.create` 被调用且返回正确格式
- **GREEN 最小实现**: `openai.OpenAI` SDK 调用，timeout=30

### T7: 内存对话管理 (P0)

- **验收条件**:
  - 同一 session 的连续消息能记住历史
  - 不同 session 互不干扰
  - 上下文窗口超过 20 轮时自动裁剪（保留最近 20 轮）
  - 裁剪后对超出上下文边界的问题做合理降级
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 多轮对话 | 第 1 条: "我叫小明" / 第 2 条: "我叫什么？" | 第 2 条回复包含"小明" | P0 |
| session 隔离 | session A 和 B 分别发消息 | A/B 的上下文不混淆 | P0 |
| 上下文裁剪 | 连续发送 25 条消息 | 保留最近 20 轮，最早 5 轮被裁剪 | P1 |
| 裁剪后降级 | 裁剪后询问被裁掉的信息 | LLM 回复"我不记得这个信息" 或类似降级 | P1 |
| 空消息 | 空白消息 | 返回提示，不调用 LLM | P1 |

- **RED 测试**: 创建 session，发送消息 "我叫小明"，再发 "我叫什么？"，验证回复引用了"小明"
- **GREEN 最小实现**: `dict[str, list]` 存储消息历史，注入 LLM 调用

### T8: 消息分发器 (P0)

- **验收条件**:
  - 从 bus 消费 inbound 消息
  - 通过对话管理获取回复
  - 发布 outbound 到 bus
  - 同一 session 的消息串行处理
  - 不同 session 可并行
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常流程 | inbound 消息 | outbound 回复发出 | P0 |
| 同 session 并发 | 快速发 2 条同 chat | 串行处理，不乱序 | P0 |
| 不同 session 并发 | chat A 和 B 同时发 | 可并行处理 | P0 |
| LLM 异常 | mock LLM 抛出异常 | 发送错误提示 outbound | P1 |

- **RED 测试**: mock 全部依赖（conftest 中定义），注入 inbound，验证 outbound 发出
- **GREEN 最小实现**: `asyncio.create_task` 包装处理协程

### T9: 入口 main() 集成 (P0)

- **验收条件**:
  - 组合所有组件并启动
  - 优雅关闭（KeyboardInterrupt 触发停止）
- **测试场景**:

| 场景 | 输入 | 预期输出 | 优先级 |
|------|------|---------|--------|
| 正常启动 | - | 所有组件初始化并运行 | P0 |
| 优雅停止 | KeyboardInterrupt | 组件逐个停止，无僵尸任务 | P1 |
| 配置错误 | 缺失必要配置 | 启动时明确报错 | P1 |

- **RED 测试**: mock 所有组件，验证启动流程
- **GREEN 最小实现**: asyncio.run(main())

## 测试执行顺序

```
Batch 1（串行按顺序）:
  先测 T0 (conftest/fixtures) → 所有其他测试依赖它
  → T3 (bus，最独立) → T1 (config) → T2 (client)
  → T6 (LLM) → T7 (session)
  → T4 (WS parser) → T5 (sender)
  → T8 (dispatcher)
  → T9 (main)

Batch 2（可并行）:
  T10 / T11 / T12 / T13 可独立测试
```

## 注意事项

- **测试环境隔离**: LLM 测试必须 mock 外部 API，避免真实调用消耗 token
- **conftest.py 是基石**: 所有 mock fixture 在 conftest.py 中全局定义，减少重复
- **飞书集成测试**: 需要真实的飞书应用凭证和测试飞书账号（标注 `@pytest.mark.integration`）
- **异步测试**: 使用 `pytest-asyncio` 的 `@pytest.mark.asyncio` 装饰器
- **会话隔离**: 测试间不能共享 session 状态，每个测试使用独立的 instance
- **Rate Limit 测试**: 使用 `responses` 或 `httpretty` 模拟 HTTP 429 响应
