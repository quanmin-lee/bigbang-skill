# Feishu LLM Bot -- Prompt 设计与关键技术细节

---

## 1. 对话上下文结构

```python
# 最终发给 LLM 的 messages 结构
messages = [
    {
        "role": "system",
        "content": system_prompt_template.format(
            bot_name="助手",
            current_date="2026-06-05",
            extra_context="..."
        )
    },
    # ...历史对话轮次（滑动窗口保留最近 N 轮）
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮你的？"},
    {"role": "user", "content": "今天天气怎么样？"},
    # 当前轮用户消息
    {"role": "user", "content": "最新的消息"}
]
```

## 2. System Prompt 模板体系

### 基础 System Prompt

```markdown
你是 {bot_name}，一个智能对话助手。
- 回复简洁、准确、友好
- 你通过飞书与用户交流
- 当前日期：{current_date}
- 如果你不知道答案，请诚实告知，不要编造信息
```

### 扩展机制

- 支持按场景附加额外 context（如知识库、用户信息、对话目标）
- 通过 `extra_context` 参数注入，拼接在 system prompt 末尾
- 不同场景可以通过不同的 prompt 模板文件名加载

## 3. 多轮对话实现细节

### 滑动窗口策略

```
保留策略：
  1. 始终保留 system prompt
  2. 从最近的对话开始保留
  3. 按 tokens 截断：总上下文不超过 max_context_tokens
  4. 至少保留最近 1 轮

实现：
  messages = [system_prompt]
  for turn in reversed(history[-max_turns:]):
      if estimated_tokens(messages) > max_context_tokens:
          break
      messages.insert(1, turn)  # 保持顺序
```

### Token 估算

- 使用 tiktoken (OpenAI) 或 Anthropic tokenizer 估算
- 设置硬上限：`max_context_tokens = model_max_tokens * 0.6`
- 保留剩余 40% 给 LLM 输出

## 4. 配置项 (`.env`)

```ini
# Feishu
FEISHU_APP_ID=cli_xxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxx

# LLM Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.7

# Conversation
CONVERSATION_STORE=redis
REDIS_URL=redis://localhost:6379/0
MAX_HISTORY_TURNS=20
SESSION_TTL_MINUTES=30
MAX_CONTEXT_TOKENS=8192

# Server
WS_APP_PORT=9000  # WebSocket 模式端口（非必须）

# Logging
LOG_LEVEL=INFO
```

## 5. 关键边界情况

| 场景 | 处理方式 |
|------|----------|
| 用户发送空消息/仅有图片 | 回复"请发送文字消息" |
| LLM 超时 (timeout > 30s) | 回复"我暂时无法回复，请稍后再试"，不保存本轮 |
| LLM 返回空内容 | 回复兜底文案 |
| 群聊中未@机器人 | 忽略事件（检查 mentions） |
| 对话上下文过长 | 自动裁剪最早的轮次 |
| 单个用户并发消息 | 按消息到达顺序串行处理（队列） |
| 飞书 Token 过期 | 自动刷新 token |
| WebSocket 断开 | 自动重连，指数退避 |

## 6. 可扩展点

- **意图识别层**：在 LLM 调用前先判断用户意图（查询、闲聊、指令），路由到不同 handler
- **工具调用 (Tool Use)**：LLM 可调用外部 API（查询天气、查数据库、发卡片等）
- **消息卡片交互**：支持按钮点击、表单提交等交互式卡片
- **知识库 RAG**：接入向量数据库，根据用户问题检索相关知识注入 context
- **多模型路由**：按场景选择不同模型（简单对话用小模型，复杂推理用大模型）
