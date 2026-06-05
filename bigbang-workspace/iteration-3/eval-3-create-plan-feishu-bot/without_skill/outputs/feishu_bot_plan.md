# 飞书机器人项目规划书

## 1. 项目概述

### 1.1 目标
构建一个飞书机器人，通过飞书 WebSocket 长连接接收用户消息，调用 LLM 生成回复，并支持多轮对话记忆。

### 1.2 核心能力
- 接收飞书用户私聊/群聊消息
- 调用 LLM（OpenAI / Claude / 等）生成自然语言回复
- 对话上下文记忆（多轮会话）
- 消息频率控制 & 错误处理
- 可扩展的插件/工具调用机制

---

## 2. 技术选型

| 组件 | 方案 | 说明 |
|------|------|------|
| 飞书 API | `lark-oapi` Python SDK | 飞书官方 SDK，支持 WebSocket 事件订阅 |
| LLM | OpenAI API / Claude API | 可切换，支持 temperature/system prompt 配置 |
| 对话存储 | SQLite（单机） / Redis（生产） | 键值对存储会话历史 |
| 运行环境 | Python 3.10+ | 异步事件驱动 |
| 部署 | systemd + uvicorn | 长驻进程，自动重启 |

---

## 3. 系统架构

```
                    ┌─────────────────────┐
                    │     飞书服务器        │
                    │  (WebSocket 网关)     │
                    └──────┬──────────────┘
                           │ 事件推送
                    ┌──────▼──────────────┐
                    │   WebSocket 连接器    │
                    │  (lark-oapi WS Client)│
                    └──────┬──────────────┘
                           │ 原始事件
                    ┌──────▼──────────────┐
                    │    消息路由器         │
                    │  - 私聊 / 群聊       │
                    │  - @机器人检测       │
                    │  - 指令识别 (/cmd)   │
                    └──────┬──────────────┘
                           │ 解析后的消息
                    ┌──────▼──────────────┐
                    │    LLM 编排层         │
                    │  - System Prompt 注入 │
                    │  - 多轮上下文组装      │
                    │  - 工具调用           │
                    └──────┬──────────────┘
                           │ LLM 回复
                    ┌──────▼──────────────┐
                    │    回复发送器         │
                    │  - 消息格式转换       │
                    │  - 频率限制           │
                    └─────────────────────┘

         ┌─────────────────────────────────────┐
         │           数据层                      │
         │  ┌──────────┐  ┌───────────────┐    │
         │  │ 会话存储  │  │ 配置 / 用户设置  │    │
         │  │ (Redis/  │  │ (YAML+SQLite)  │    │
         │  │  SQLite) │  │               │    │
         │  └──────────┘  └───────────────┘    │
         └─────────────────────────────────────┘
```

---

## 4. 目录结构

```
feishu-bot/
├── pyproject.toml              # 项目依赖与元数据
├── .env.example                # 环境变量模板
├── config/
│   ├── bot.yaml                # 机器人通用配置
│   └── prompts/
│       └── system.md           # 系统级 System Prompt
├── src/
│   ├── __init__.py
│   ├── main.py                 # 入口：启动 WS 连接
│   ├── bot.py                  # 飞书事件处理（消息接收）
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py           # LLM API 调用封装
│   │   ├── provider.py         # 多 provider 抽象（OpenAI/Claude）
│   │   └── prompts.py          # Prompt 模板管理
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── store.py            # 会话存储抽象接口
│   │   ├── sqlite_store.py     # SQLite 实现
│   │   └── redis_store.py      # Redis 实现（可选）
│   ├── router/
│   │   ├── __init__.py
│   │   ├── dispatcher.py       # 消息分发
│   │   └── commands.py         # 指令处理 (/help, /clear 等)
│   └── utils/
│       ├── __init__.py
│       ├── config.py           # 配置加载
│       └── rate_limiter.py     # 频率限制
└── tests/
    ├── test_llm.py
    ├── test_memory.py
    └── test_router.py
```

---

## 5. 核心模块设计

### 5.1 飞书事件连接 (`src/bot.py`)

```python
# 伪代码示意
class FeishuBotHandler:
    """飞书机器人消息处理器"""

    def __init__(self, app_id, app_secret):
        self.client = LarkClient(app_id, app_secret)
        # 注册事件处理器
        self.client.on("event:im.message.receive_v1", self.on_message)

    async def on_message(self, event):
        """收到消息时的回调"""
        message = event.message
        msg_type = message.message_type  # text / image / interactive
        chat_type = message.chat_type    # p2p / group
        content = parse_content(message)

        # 路由到消息分发器
        await dispatcher.handle(message_id, sender_id, chat_type, content)
```

**关键点：**
- 使用 `lark-oapi` 的 WebSocket 模式（`ws://`），无需暴露公网 Webhook
- 自动注册事件回调，SDK 管理心跳和重连
- 区分私聊 (`p2p`) 和群聊 (`group`)，群聊需检测 `@bot`

### 5.2 消息路由 (`src/router/dispatcher.py`)

```python
class MessageDispatcher:
    """消息分发器：决定如何响应每条消息"""

    def __init__(self, llm_client, memory_store, commands):
        self.llm = llm_client
        self.memory = memory_store
        self.commands = commands  # 指令路由表

    async def handle(self, msg_id, sender_id, chat_type, content):
        # 1. 频率检查
        if not rate_limiter.check(sender_id):
            return send_text(msg_id, "消息发送太快了，请稍后再试")

        # 2. 指令检测
        if content.startswith("/"):
            cmd = parse_command(content)
            handler = self.commands.get(cmd.name)
            if handler:
                return await handler.execute(cmd.args, sender_id, chat_type)

        # 3. LLM 处理
        reply = await self.llm.generate(sender_id, content)
        await send_reply(msg_id, reply)
```

**路由规则：**

| 条件 | 行为 |
|------|------|
| 消息以 `/` 开头 | 指令处理 |
| 群聊且未 `@bot` | 忽略 |
| 私聊 | 正常 LLM 回复 |
| 群聊且包含 `@bot` | LLM 回复（自动去除 `@` 内容） |

### 5.3 LLM 调用层 (`src/llm/client.py`)

```python
class LLMClient:
    """LLM 调用封装，支持多 provider 切换"""

    def __init__(self, provider: str, config: dict):
        # provider: "openai" | "claude"
        self.api = create_provider(provider, config)

    async def generate(self, session_id: str, user_message: str) -> str:
        # 1. 获取会话历史
        history = await memory_store.get_history(session_id)

        # 2. 组装 messages（含 system prompt）
        messages = self._build_messages(history, user_message)

        # 3. 调用 LLM
        response = await self.api.chat(messages)

        # 4. 保存本轮对话
        await memory_store.append(session_id, user_message, response)

        return response
```

**Provider 抽象：**

```python
class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list) -> str: ...

class OpenAIProvider(LLMProvider):
    def __init__(self, config):
        self.client = OpenAI(api_key=config["api_key"])
        self.model = config.get("model", "gpt-4o")

    async def chat(self, messages):
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
        )
        return resp.choices[0].message.content

class ClaudeProvider(LLMProvider):
    def __init__(self, config):
        self.client = Anthropic(api_key=config["api_key"])
        self.model = config.get("model", "claude-sonnet-4-20250514")

    async def chat(self, messages):
        # 将 OpenAI 格式转成 Anthropic 格式
        claude_messages = convert_to_claude_format(messages)
        resp = await self.client.messages.create(
            model=self.model,
            system=extract_system_prompt(messages),
            messages=claude_messages,
            max_tokens=4096,
        )
        return resp.content[0].text
```

### 5.4 对话记忆 (`src/memory/store.py`)

**存储接口：**

```python
class MemoryStore(ABC):
    @abstractmethod
    async def get_history(self, session_id: str, limit: int = 20) -> list: ...
    @abstractmethod
    async def append(self, session_id: str, user_msg: str, bot_reply: str): ...
    @abstractmethod
    async def clear(self, session_id: str): ...
```

**SQLite 实现设计：**

```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    role TEXT NOT NULL,  -- 'user' | 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 查询最近 N 条消息
SELECT role, content FROM messages
WHERE session_id = ?
ORDER BY created_at DESC
LIMIT ?;
```

**会话窗口管理：**
- 保留最近 20 轮对话（可配置）
- 超出窗口则丢弃最早的轮次
- 上下文总 token 数超过阈值时压缩历史

### 5.5 指令系统 (`src/router/commands.py`)

```python
@command("help")
async def cmd_help(args, sender_id, chat_type):
    return """🤖 **机器人帮助**
/help     - 显示此帮助
/clear    - 清除对话历史
/prompt   - 查看当前系统提示词
/mode     - 切换对话模式"""

@command("clear")
async def cmd_clear(args, sender_id, chat_type):
    await memory_store.clear(session_id(sender_id))
    return "✅ 对话历史已清除"

@command("prompt")
async def cmd_prompt(args, sender_id, chat_type):
    return f"当前系统提示词：\n{get_current_system_prompt()}"
```

---

## 6. 多轮对话设计

### 6.1 Session 生命周期

```
用户发消息 ──→ 查找/创建 session
                  │
          ┌───────┴───────┐
          │               │
      session 存在     session 不存在
          │               │
    加载历史消息     创建新 session
          │          注入 system prompt
          └───────┬───────┘
                  │
          组装 messages 列表
                  │
           ┌──────▼──────┐
           │   LLM 调用   │
           └──────┬──────┘
                  │
            保存到历史
                  │
             返回回复
```

### 6.2 Session key 生成策略

| 场景 | Session Key | 说明 |
|------|-------------|------|
| 私聊 | `p2p:{user_id}` | 同一用户的所有对话共用上下文 |
| 群聊 @bot | `group:{chat_id}:{user_id}` | 群聊中每个用户独立上下文 |

### 6.3 上下文 Token 控制

```python
MAX_TOKENS = 4096      # 模型上下文窗口上限
RESERVE_TOKENS = 1024  # 预留 token（用于回复生成）
MAX_HISTORY = 20       # 保留最大轮数

async def build_messages(session_id: str, new_message: str) -> list:
    system = await load_system_prompt()
    history = await memory_store.get_history(session_id, MAX_HISTORY)

    messages = [{"role": "system", "content": system}]
    for h in history:
        messages.append({"role": "user", "content": h.user_msg})
        messages.append({"role": "assistant", "content": h.bot_reply})

    # 估算 token，超出则截断早期历史
    while estimate_tokens(messages) > (MAX_TOKENS - RESERVE_TOKENS):
        # 丢弃最早的一轮（保留 system prompt）
        if len(messages) > 2:
            messages.pop(1)  # 最早 user msg
            messages.pop(1)  # 对应 assistant reply
        else:
            break

    messages.append({"role": "user", "content": new_message})
    return messages
```

---

## 7. 错误处理

| 场景 | 处理方式 |
|------|---------|
| 飞书 WebSocket 断开 | lark-oapi 自动重连，指数退避 |
| LLM API 超时 | 重试 2 次，告知用户"服务繁忙" |
| LLM 返回空/无效内容 | 兜底回复"暂时无法回答" |
| 消息发送失败 | 异步重试队列 |
| 频率过高 | 返回频率限制提示，不调用 LLM |

---

## 8. 配置设计 (`config/bot.yaml`)

```yaml
feishu:
  app_id: "cli_xxxxxx"
  app_secret: "xxxxxxxx"

llm:
  provider: "openai"         # openai | claude
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4o"
    temperature: 0.7
    max_tokens: 2048
  claude:
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-sonnet-4-20250514"
    temperature: 0.7
    max_tokens: 4096

memory:
  backend: "sqlite"          # sqlite | redis
  sqlite:
    path: "data/conversations.db"
  redis:
    host: "localhost"
    port: 6379
    ttl: 86400               # 会话过期时间（秒）

bot:
  max_history: 20            # 保留的最大对话轮数
  max_tokens: 4096           # 上下文窗口 token 上限
  rate_limit:
    per_user: 10             # 每分钟每用户最多 10 条
    per_global: 100          # 全局每分钟最多 100 条
  allow_private_chat: true
  allow_group_chat: true
  group_mention_only: true   # 群聊仅响应 @bot 消息
```

---

## 9. 部署方案

### 9.1 systemd 服务

```ini
[Unit]
Description=Feishu Bot Service
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/opt/feishu-bot
EnvironmentFile=/opt/feishu-bot/.env
ExecStart=/opt/feishu-bot/.venv/bin/python -m src.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 9.2 环境变量 (`.env`)

```
FEISHU_APP_ID=cli_xxxxxx
FEISHU_APP_SECRET=xxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
LOG_LEVEL=INFO
```

---

## 10. 实现路线图

### Phase 1: 基础骨架（Day 1-2）
- [ ] 项目初始化、依赖配置
- [ ] 飞书 WebSocket 连接建立
- [ ] 消息接收与简单回复（echo）
- [ ] 部署到服务器验证连通性

### Phase 2: LLM 集成（Day 3-4）
- [ ] LLM Provider 抽象 + OpenAI 实现
- [ ] Claude Provider 实现
- [ ] System Prompt 加载与管理
- [ ] 基础问答功能

### Phase 3: 多轮对话（Day 5-6）
- [ ] SQLite 记忆存储
- [ ] Session 管理
- [ ] 上下文组装与 Token 控制
- [ ] 历史清理与过期策略

### Phase 4: 指令与增强（Day 7-8）
- [ ] 指令系统 (`/help`, `/clear` 等)
- [ ] 群聊 @bot 识别
- [ ] 频率限制
- [ ] 错误处理与重试

### Phase 5: 生产化（Day 9-10）
- [ ] systemd 服务配置
- [ ] 日志与监控
- [ ] 可选 Redis 存储迁移
- [ ] 压力测试与优化

---

## 11. 依赖清单 (`pyproject.toml`)

```toml
[project]
name = "feishu-bot"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "lark-oapi>=1.0.0",
    "openai>=1.0.0",
    "anthropic>=0.30.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.25.0",
]

[project.optional-dependencies]
redis = ["redis>=5.0.0"]
dev = ["pytest>=7.0", "pytest-asyncio>=0.21.0", "black", "ruff"]
```

---

## 12. 关键注意事项

1. **飞书 WebSocket 模式无需公网 IP**：这是相比 Webhook 的最大优势，适合内网开发环境
2. **API 频率限制**：飞书发送消息 API 有频率限制（一般 5次/秒），需要加本地排队
3. **长回复分段**：LLM 回复超过 2000 字需分段发送（飞书单条消息长度限制）
4. **消息格式**：支持 `text` 和 `post`（富文本）两种格式，`post` 支持 Markdown 样式的文本排版
5. **敏感词过滤**：飞书平台侧会对消息进行敏感词审核，需关注失败回调
6. **Session 隔离**：群聊中不同用户的上下文必须隔离
7. **重入保护**：LLM 超时重试时避免重复 append 对话历史

---

## 13. 扩展方向（未来规划）

- **工具调用 / Function Calling**：让 LLM 可以查询数据库、调用 API
- **多模态输入**：支持接收图片，调用多模态模型分析
- **工作流集成**：通过飞书卡片消息构建交互式工作流
- **知识库 RAG**：接入向量数据库，基于企业知识库问答
- **多机器人**：不同频道配置不同 Prompt / 能力
