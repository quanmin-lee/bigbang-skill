# 审查意见 - 第 1 轮

## 架构评估 (ARCH.md)

- ✅ 通过 — 需求理解准确，模块划分清晰（消息接收、会话管理、LLM 调用、回复发送）
- ✅ 通过 — 关键数据流描述完整，从飞书用户到回复的闭环清晰
- ✅ 通过 — V1 最小主链定义合理，6 个改动点覆盖了端到端链路的必要组件
- ⚠️ 建议 — 缺少"错误处理"在架构图中的显式位置。所有模块之间的连线都应标注异常处理路径（超时、限频、认证失败）
- ⚠️ 建议 — 缺少"配置管理"模块的详细设计。飞书机器人需要：App ID、App Secret、Verification Token、Encrypt Key、LLM API Key 等配置，建议明确配置加载策略（环境变量 vs 配置文件）
- ⚠️ 建议 — 风险部分第 3 点"签名验证"建议升为高风险并增加缓解措施说明

## 执行计划 (EXECUTION_PLAN.md)

- ✅ 通过 — 任务分解粒度合理，10 个任务覆盖了 V1 主链和 V2 增强
- ✅ 通过 — 依赖关系分析正确（T1 须先完成，T2/T4/T5/T6 可并发）
- ✅ 通过 — 批次分组合理，Batch 1 打通主链，Batch 2 完善功能
- ⚠️ 建议 — T3 的"消息解析与处理编排"描述偏笼统。编排器应明确定义接口契约：它接收什么（解析后的事件对象）、调用什么（SessionManager.get_context → LLMService.generate → MessageSender.send → SessionManager.update_context）、输出什么
- ⚠️ 建议 — 缺少飞书 Event Subscription 的配置说明。飞书控制台需要配置回调 URL，这个"部署配置"应该作为 T0 或 T7 的一部分
- ⚠️ 建议 — 没有显式的"飞书 Token 管理"任务。Token 自动刷新是发送消息的前置条件，应在 T6 中明确标注为子任务

## 测试边界 (TEST_BOUNDARIES.md)

- ✅ 通过 — P0 测试覆盖了所有 CRITICAL_PATH 任务，验收条件清晰
- ✅ 通过 — Mock 策略正确（外部 API 全 mock, 测试独立于网络）
- ✅ 通过 — 测试执行顺序合理，标注了并发可能性
- ⚠️ 建议 — T2 中 URL Challenge 验证：飞书用的是 GET 请求 + query param，但也有可能是 POST + body JSON。建议覆盖两种 challenge 验证场景
- ⚠️ 建议 — T7 E2E 测试需要更精确：应该验证 LLM 被调用时的具体消息内容（System Prompt + 用户消息格式是否正确），而非仅仅验证"被调用"
- ⚠️ 建议 — 缺少"并发消息"测试场景：当同一用户快速发送多条消息时，会话上下文是否正确维护（竞态条件风险）

## 综合判定

- **状态**: ⚠️ 需要第 2 轮
- **裁决说明**:
  - 架构方面需要补充：错误处理路径、配置管理设计、Token 管理任务
  - 执行计划需要补充：飞书控制台配置说明、Token 管理作为显式任务、编排器接口契约
  - 测试需要补充：Challenge 验证的双模式、E2E 中消息内容验证、并发消息场景

### 本轮已解决问题
（首轮审查，无上一轮问题）

### 本轮遗留问题
1. 架构缺少"错误处理路径"和"配置管理"的详细设计
2. 执行计划缺少 Token 管理作为显式任务
3. 测试缺少并发消息场景

---

## 合并建议

### 架构决策（来自 ARCH.md）

1. **模块化分层**: 采用五层架构——消息接收层（FastAPI 路由/验签）、会话管理层（上下文存储）、LLM 调用层（API 封装）、回复发送层（飞书消息 API）、配置管理层（统一配置加载）
2. **技术栈**: Python 3.11+ / FastAPI / lark-oapi / OpenAI SDK / SQLite(dev) 或 Redis(prod)
3. **核心数据流**: 飞书用户 → Webhook → 验签 → 会话上下文 → LLM 生成 → 飞书消息发送 → 用户收到回复

### 执行计划（来自 EXECUTION_PLAN.md）

**Batch 1 (CRITICAL_PATH)**:
- T1: 项目初始化 (串行入口)
- T2: 飞书路由+验签 [parallel]
- T4: 会话管理器 [parallel]
- T5: LLM 调用服务 [parallel]
- T6: 消息发送服务 [parallel] — **含 Token 管理子任务**
- T3: 消息编排 (依赖 T2/T4/T5/T6)
- T7: E2E 集成验证 (依赖 T3)

**Batch 2 (ENHANCEMENT)**:
- T8: 上下文截断
- T9: 重试机制
- T10: 日志监控

### 测试策略（来自 TEST_BOUNDARIES.md）

- **框架**: pytest + pytest-asyncio + pytest-mock
- **Mock 策略**: 飞书 API 和 LLM API 全部 Mock，不依赖外部服务
- **P0 测试**: 覆盖 Batch 1 全部 7 个任务，验收条件包含正常路径和错误路径
- **执行顺序**: T1 → 并发(T2/T4/T5/T6) → T3 → T7 → 并发(T8/T9/T10)

### 输入/输出契约

| 模块 | 输入 | 输出 |
|------|------|------|
| EventRouter | 飞书 HTTP 回调 (含签名) | 解析后的事件对象 (MessageEvent) |
| SessionManager | user_id | Session 对象 (含消息列表) |
| LLMService | 消息列表 [System + User + Assistant] | LLM 回复文本 |
| MessageSender | user_id + 消息文本 | 飞书 API 响应 |
| Handler | MessageEvent | (编排各模块, 无直接输出) |

### 关键风险提醒

1. **飞书签名验证是安全底线** — 必须在处理任何消息前强制验证，防止伪造请求。建议使用 Feishu SDK 内置验证
2. **Token 自动刷新不可遗漏** — tenant_access_token 有效期 2 小时，T6 必须实现静默刷新，否则生产环境每小时断连一次
3. **多轮对话上下文长度控制** — V1 就应实现基础窗口截断（如保留最近 10 轮对话），防止 Token 消耗失控
