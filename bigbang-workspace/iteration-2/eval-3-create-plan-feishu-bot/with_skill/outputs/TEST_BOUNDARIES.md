# 测试验收边界

## 测试策略

| 层面 | 框架/工具 | 范围 |
|------|----------|------|
| 单元测试 | pytest | 各模块独立测试（会话管理、LLM 调用、消息格式化） |
| 集成测试 | pytest + httpx | 飞书回调路由、编排流程、E2E 链路 |
| Mock 策略 | pytest-mock / unittest.mock | 飞书 API、LLM API 全部 mock，不依赖外部服务 |
| 测试框架 | pytest + pytest-asyncio | 全部异步测试 |

测试原则：
- **所有外部依赖都 Mock**：飞书 API、LLM API 都在测试中 Mock
- **P0 测试必须可独立运行**：不依赖服务启动、不依赖网络
- **每个任务从 RED 测试开始**：先写会失败的测试，再写实现

## 按任务分解

### T1: 项目初始化与依赖配置 (P0)

- **验收条件**:
  - 项目可 `pip install -e .` 安装
  - 所有依赖可正常导入
  - 目录结构完整
- **测试场景**:
  | 场景 | 输入 | 预期输出 | 优先级 |
  |------|------|---------|--------|
  | 导入测试 | `from app.config import settings` | 正常导入无报错 | P0 |
  | 目录完整性 | 检查目录树 | 所有模块目录存在 | P0 |
- **RED 测试**: 编写 `test_imports.py` 验证各模块可导入（会因模块未实现而失败）
- **GREEN 最小实现**: 创建目录结构 + `__init__.py` + 空模块文件

### T2: 飞书事件路由+签名验证 (P0)

- **验收条件**:
  - `/webhook/event` POST 端点可接收飞书回调
  - 签名验证正确处理合法/非法请求
  - 正确解析 `im.message.receive_v1` 事件
  - 返回飞书要求的 Challenge 验证响应
- **测试场景**:
  | 场景 | 输入 | 预期输出 | 优先级 |
  |------|------|---------|--------|
  | URL Challenge 验证 | GET 请求带 challenge 参数 | 返回 challenge 原值 | P0 |
  | 合法事件回调 | 模拟飞书消息事件的 POST 请求 | HTTP 200 | P0 |
  | 签名错误请求 | 错误签名的 POST 请求 | HTTP 403 | P0 |
  | 无效事件类型 | 非消息事件的 POST | HTTP 200 (忽略) | P1 |
- **RED 测试**: `test_router.py` — 发送模拟飞书回调 POST 请求，断言 200 响应
- **GREEN 最小实现**: FastAPI router + 签名验证中间件 + 事件解析

### T3: 消息解析与处理编排 (P0)

- **验收条件**:
  - 从飞书事件中正确提取文本消息内容
  - 正确识别发送者 ID、聊天类型（单聊/群聊）
  - 完整编排：获取上下文 → LLM 调用 → 发送回复 → 更新上下文
- **测试场景**:
  | 场景 | 输入 | 预期输出 | 优先级 |
  |------|------|---------|--------|
  | 正常消息处理 | 模拟文本消息事件 | LLM 被调用 + 回复被发送 | P0 |
  | 空消息处理 | 空文本消息 | 返回错误提示，不调用 LLM | P1 |
  | 只含空格的文本 | "   " | 同空消息处理 | P1 |
  | 群聊消息 | 群聊事件（chat_type=group） | 正确识别 chat_type | P1 |
- **RED 测试**: `test_handler.py` — mock SessionManager + LLMService + MessageSender，发送模拟消息事件，验证 LLM 被调用
- **GREEN 最小实现**: handler 函数编排各模块调用

### T4: 会话管理器（内存存储） (P0)

- **验收条件**:
  - 新用户首次发送消息时创建新会话
  - 已有会话的用户获取历史上下文
  - 会话超过 TTL 后自动清理
  - 上下文消息按顺序保存
- **测试场景**:
  | 场景 | 输入 | 预期输出 | 优先级 |
  |------|------|---------|--------|
  | 新会话创建 | `get_context("user_a")` | 返回空消息列表的新会话 | P0 |
  | 已有会话 | 先添加消息，再 `get_context` | 返回含历史消息的会话 | P0 |
  | 多用户隔离 | user_a 和 user_b 各自会话 | 互不影响 | P0 |
  | 会话 TTL 过期 | 会话超过 30 分钟未活动 | `get_context` 自动清理 | P1 |
  | 消息追加 | `add_message(session_id, msg)` | 消息出现在历史中 | P0 |
- **RED 测试**: `test_session_manager.py` — 创建 SessionManager，获取新用户上下文，断言返回空列表
- **GREEN 最小实现**: SessionManager + Session dataclass + 内存 dict 存储

### T5: LLM 调用服务 (P0)

- **验收条件**:
  - 正确组装 System Prompt + 对话历史 + 当前消息
  - 成功调用 LLM API 并返回文本回复
  - API 超时时抛出明确异常
  - API 调用失败时返回可处理的错误信息
- **测试场景**:
  | 场景 | 输入 | 预期输出 | 优先级 |
  |------|------|---------|--------|
  | 正常 LLM 调用 | 消息列表 + 模型配置 | 返回回复文本 | P0 |
  | Prompt 组装 | System + 历史 + 当前消息 | 正确的消息列表格式 | P0 |
  | API 超时 | mock 超时异常 | 抛出 TimeoutError | P0 |
  | API 返回空 | mock 空回复 | 返回默认提示文本 | P1 |
  | API 服务器错误 | mock 500 错误 | 抛出 APIError | P1 |
- **RED 测试**: `test_llm_service.py` — mock OpenAI/Anthropic client，调用 generate，断言返回非空字符串
- **GREEN 最小实现**: LLMService 类 + API 封装 + 超时控制

### T6: 消息发送服务 (P0)

- **验收条件**:
  - 正确调用飞书 Send Message API
  - 成功发送文本消息
  - Token 过期时自动刷新
  - API 调用失败时抛出异常
- **测试场景**:
  | 场景 | 输入 | 预期输出 | 优先级 |
  |------|------|---------|--------|
  | 发送文本消息 | user_id + 文本 | 飞书 API 被正确调用 | P0 |
  | Token 过期自动刷新 | mock 401 响应 | 自动刷新 Token 后重试 | P1 |
  | 发送 API 错误 | mock 500 响应 | 抛出 SendMessageError | P1 |
  | 消息内容为空 | 空字符串文本 | 不发送，返回 False | P1 |
- **RED 测试**: `test_sender.py` — mock lark-oapi client，调用 send_text，断言 API 被调用
- **GREEN 最小实现**: MessageSender 类 + 飞书 API 调用 + Token 管理

### T7: 主链路集成与 E2E 验证 (P0)

- **验收条件**:
  - FastAPI app 可正常启动
  - 路由注册正确
  - 模拟完整消息流程：事件接收 → LLM 调用 → 消息发送
- **测试场景**:
  | 场景 | 输入 | 预期输出 | 优先级 |
  |------|------|---------|--------|
  | 完整 E2E 流程 | 模拟飞书消息事件 | LLM 被调用 + 发送 API 被调用 | P0 |
  | 健康检查 | GET /health | HTTP 200 + {"status": "ok"} | P0 |
  | 无效路由 | GET /invalid | HTTP 404 | P1 |
- **RED 测试**: `test_e2e.py` — TestClient 发送 POST 到 `/webhook/event`，断言返回 200
- **GREEN 最小实现**: main.py 组装 FastAPI app + 注册 router

### T8: 多轮对话上下文截断策略 (P1)

- **验收条件**:
  - 超出 Token 上限时自动截断最早的消息
  - 保留 System Prompt 不受截断影响
  - 滑动窗口保留最近 N 轮对话
- **测试场景**:
  | 场景 | 输入 | 预期输出 | 优先级 |
  |------|------|---------|--------|
  | 正常截断 | N+1 轮对话历史 | 最早 1 轮被移除 | P1 |
  | 系统提示保留 | 满 Token 时截断 | System Prompt 不被移除 | P1 |
  | 空历史不截断 | 无消息历史 | 不执行任何操作 | P2 |
- **RED 测试**: `test_context_truncation.py` — 写入超过窗口大小的消息，断言最早消息被丢弃

### T9: 错误处理与重试机制 (P1)

- **验收条件**:
  - LLM 调用失败后最多重试 3 次
  - 重试间隔指数退避
  - 最终失败时返回用户友好的错误消息
- **测试场景**:
  | 场景 | 输入 | 预期输出 | 优先级 |
  |------|------|---------|--------|
  | 重试 3 次后成功 | 前 2 次失败，第 3 次成功 | 返回成功回复 | P1 |
  | 3 次均失败 | 全部失败 | 返回友好错误提示 | P1 |
  | 指数退避验证 | 连续失败 | 间隔时间递增 | P2 |
- **RED 测试**: `test_retry.py` — mock LLM API 前 n 次失败，断言重试逻辑触发

### T10: 日志与监控 (P2)

- **验收条件**:
  - 每个请求/响应有结构化日志
  - LLM 调用延迟和 Token 消耗被记录
- **测试场景**:
  | 场景 | 输入 | 预期输出 | 优先级 |
  |------|------|---------|--------|
  | 请求日志 | 模拟请求 | 日志包含 request_id, user_id | P2 |
  | 性能日志 | LLM 调用完成 | 日志包含 latency, token_count | P2 |
- **RED 测试**: `test_logging.py` — 验证 logger handler 配置正确

## 测试执行顺序

```
T1 (初始化, P0)
 │
 ├── T2 (路由, P0)  ← 可并发
 ├── T4 (会话, P0)  ← 可并发
 ├── T5 (LLM, P0)   ← 可并发
 └── T6 (发送, P0)  ← 可并发
 │
 └── T3 (编排, P0)  ← 依赖 T2, T4, T5, T6
      │
      └── T7 (E2E, P0)  ← 依赖 T3
           │
           ├── T8 (截断, P1)  ← 依赖 T4, T5
           ├── T9 (重试, P1)  ← 依赖 T5, T6
           └── T10 (日志, P2) ← 依赖 T7
```

## 注意事项

1. **所有外部 API 必须 Mock**: 飞书 API 和 LLM API 的测试都不应产生真实调用
2. **异步测试**: 使用 `pytest-asyncio` + `@pytest.mark.asyncio` 装饰器
3. **Config Mock**: 测试中使用独立的测试配置（Mock Token、Mock API Key）
4. **会话隔离**: 测试用例之间不应共享会话状态，每个测试独立创建 SessionManager
5. **Token 自动刷新**: 飞书 token 刷新逻辑需要单独测试，不要在 E2E 中依赖
