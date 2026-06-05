# Feishu LLM Bot -- 执行计划

## 阶段划分

### Phase 0: 项目初始化 (0.5天)

- [ ] 创建项目目录结构
- [ ] 初始化 Python 虚拟环境
- [ ] 安装依赖：`lark-oapi`, `openai`, `redis`, `loguru`, `pydantic`
- [ ] 创建飞书应用、获取 App ID / App Secret
- [ ] 配置事件订阅（WebSocket 或 Webhook）
- [ ] 配置 `.env` 环境变量模板

### Phase 1: 消息接收 (1天)

- [ ] 实现 WebSocket 长连接启动 (`ws.py`)
- [ ] 注册 `im.message.receive_v1` 事件处理器
- [ ] 解析消息结构：sender, chat_type, text content
- [ ] 过滤自循环消息（跳过机器人自己的消息）
- [ ] 单元测试：mock Feishu 事件验证解析逻辑
- [ ] 验证：在飞书中@机器人发送消息，确认收到事件

### Phase 2: 对话管理 (1天)

- [ ] 实现 `ConversationStore` 抽象接口
- [ ] 实现 `MemoryConversationStore`（内存，开发用）
- [ ] 实现 `RedisConversationStore`（生产用）
- [ ] 定义数据模型：`Message` (role, content, timestamp), `Session`
- [ ] 滑动窗口逻辑：保留最近 N 轮 (user+assistant)
- [ ] TTL 过期清理策略
- [ ] 单元测试：多轮消息追加、窗口裁剪、过期

### Phase 3: LLM 服务 (1.5天)

- [ ] 实现 `LLMProvider` 抽象基类
- [ ] 实现 `OpenAIProvider` (兼容 OpenAI / Azure / 通义千问)
- [ ] 实现 `ClaudeProvider` (可选)
- [ ] Prompt 模板系统：按场景加载不同 system prompt
- [ ] 同步回复模式
- [ ] 流式回复模式（可选，推荐）
- [ ] 错误处理：超时、API 错误、兜底回复
- [ ] 单元测试：mock LLM API 验证回复生成

### Phase 4: 回复发送 (0.5天)

- [ ] 飞书 `send_message` API 封装
- [ ] 文本消息发送
- [ ] 富文本消息发送
- [ ] 流式消息逐步推送（先占位后更新）
- [ ] 错误消息兜底回复

### Phase 5: 集成联调 (1天)

- [ ] 完整链路：收到消息 → 加载上下文 → 调用 LLM → 发送回复 → 保存上下文
- [ ] 私聊场景测试
- [ ] 群聊场景测试（@机器人）
- [ ] 多轮对话连续性测试
- [ ] 异常情况测试：LLM 超时、网络断开、重连

### Phase 6: 部署上线 (0.5天)

- [ ] systemd service 配置 / Dockerfile
- [ ] 日志配置（loguru + 日志轮转）
- [ ] 启动脚本 + 健康检查
- [ ] 监控告警
- [ ] 灰度发布 & 全量上线

---

## 总计预估：约 5 人天

## 目录结构规划

```
feishu-llm-bot/
├── .env.example
├── requirements.txt
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── main.py              # 入口：启动 WebSocket / Webhook server
│   ├── config.py             # 配置加载（.env + pydantic Settings）
│   ├── receiver.py           # 消息接收（事件处理器）
│   ├── conversation.py       # 对话管理
│   ├── llm_service.py        # LLM provider 抽象与实现
│   ├── sender.py             # 消息发送
│   ├── prompt.py             # Prompt 模板管理
│   └── models.py             # 数据模型
├── tests/
│   ├── test_receiver.py
│   ├── test_conversation.py
│   ├── test_llm_service.py
│   └── test_sender.py
└── deploy/
    ├── Dockerfile
    ├── systemd.service
    └── nginx.conf
```
