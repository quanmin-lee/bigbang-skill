# 执行计划

## 任务总览

| ID | 任务名 | 类型 | 前置依赖 | 涉及文件 |
|----|--------|------|---------|---------|
| T1 | 项目初始化与依赖配置 | [CRITICAL_PATH] | 无 | `pyproject.toml`, `requirements.txt` |
| T2 | 飞书事件路由+签名验证 | [CRITICAL_PATH] | T1 | `app/config.py`, `app/router.py` |
| T3 | 消息解析与处理编排 | [CRITICAL_PATH] | T2 | `app/handler.py` |
| T4 | 会话管理器（内存存储） | [CRITICAL_PATH] | T1 | `app/session/manager.py`, `app/session/models.py` |
| T5 | LLM 调用服务 | [CRITICAL_PATH] | T1 | `app/llm/service.py`, `app/llm/prompts.py` |
| T6 | 消息发送服务 | [CRITICAL_PATH] | T2 | `app/sender.py` |
| T7 | 主链路集成与 E2E 验证 | [CRITICAL_PATH] | T3, T4, T5, T6 | `app/main.py`, `tests/test_e2e.py` |
| T8 | 多轮对话上下文截断策略 | [ENHANCEMENT] | T4, T5 | `app/session/store.py` |
| T9 | 错误处理与重试机制 | [ENHANCEMENT] | T5, T6 | `app/llm/service.py`, `app/sender.py` |
| T10 | 日志与监控 | [ENHANCEMENT] | T7 | `app/logging.py` |

## 批次规划

### Batch 1: [CRITICAL_PATH] 打通主链

**T1: 项目初始化与依赖配置**
- 创建 `pyproject.toml` (Python 3.11+)
- 安装依赖: fastapi, uvicorn, lark-oapi, openai (或 anthropic), pydantic
- 创建目录结构:
  ```
  app/
    __init__.py
    config.py
    router.py
    handler.py
    sender.py
    session/
      __init__.py
      models.py
      manager.py
    llm/
      __init__.py
      service.py
      prompts.py
  tests/
    __init__.py
  ```

**T2: 飞书事件路由+签名验证** [parallel with T4, T5, T6]
- 实现 `/webhook/event` 端点
- 实现飞书 Event Callback 签名验证
- 解析 `im.message.receive_v1` 事件
- 提取消息内容、发送者、聊天类型

**T3: 消息解析与处理编排** (depends on T2)
- 从事件中提取文本消息内容
- 调用会话管理器获取/创建上下文
- 调用 LLM 服务生成回复
- 调用消息服务发送回复
- 更新会话上下文

**T4: 会话管理器（内存存储）** [parallel with T2, T5, T6]
- 定义会话数据结构 (`Session`, `Message`)
- 实现内存存储（`dict[user_id, Session]`）
- 实现会话 TTL 过期清理（30 分钟无活动自动清除）
- 实现上下文消息列表管理（追加/读取）

**T5: LLM 调用服务** [parallel with T2, T4, T6]
- 封装 LLM API（OpenAI 兼容接口）
- 组装 System Prompt + 对话历史
- 实现超时控制（30s）
- 解析 LLM 回复文本

**T6: 消息发送服务** [parallel with T2, T4, T5]
- 封装飞书 Send Message API
- 支持文本消息发送
- 处理 Token 自动刷新

**T7: 主链路集成与 E2E 验证** (depends on T3, T4, T5, T6)
- 组装 `main.py` FastAPI app
- 注册路由
- E2E 测试：模拟飞书回调 → 验证 LLM 调用 → 验证消息发送

### Batch 2: [ENHANCEMENT] 功能完善

**T8: 多轮对话上下文截断策略** (depends on T4, T5)
- 实现 Token 计数估算
- 实现滑动窗口截断（保留最近 N 轮 + 系统提示）
- 支持超长上下文自动摘要

**T9: 错误处理与重试机制** (depends on T5, T6)
- LLM 调用失败重试（指数退避，最多 3 次）
- 飞书 API 调用失败重试
- 用户友好的错误回复

**T10: 日志与监控** (depends on T7)
- 结构化日志（JSON 格式）
- 请求/响应日志
- 性能指标记录（LLM 延迟、Token 消耗）

## 依赖图

```
T1 (项目初始化)
 │
 ├──────────┬──────────┬──────────┐
 │          │          │          │
 ▼          ▼          ▼          ▼
T2 (路由)  T4 (会话)  T5 (LLM)  T6 (发送)
 │          │          │          │
 └──────────┼──────────┼──────────┘
            ▼          ▼          ▼
           T3 (编排) ←────────────┘
                 │
                 ▼
                T7 (集成)
                 │
          ┌──────┴──────┐
          ▼             ▼
         T8 (截断)     T9 (重试)
          │             │
          └──────┬─────┘
                 ▼
               T10 (日志)
```

Batch 1 内: T2, T4, T5, T6 可并行（无数据依赖，修改不同文件）
Batch 1 串行部分: T1 → [并行] → T3 → T7

## 风险与注意事项

1. **T2 签名验证是安全底线**: 必须先实现签名验证再处理消息，防止伪造请求
2. **T5 LLM 超时**: 必须设置合理的超时时间（默认 30s），超时后返回用户友好提示
3. **T4 内存存储限制**: V1 使用内存存储，重启后会话丢失，需告知用户此限制
4. **T3 编排中错误处理**: 任何环节失败都应给用户回复而不是静默失败
5. **飞书 API Token**: 需要实现 tenant_access_token 缓存和自动刷新，否则每小时会断
