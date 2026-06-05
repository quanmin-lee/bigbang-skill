# BigBang Skill

轻量级 Claude Code 工作流工具包，提供项目规划与并发执行两大能力。

## 安装

```bash
# 方式一：直接安装 .skill 文件
# 在 Claude Code 中运行：
# /install-skill path/to/bigbang.skill

# 方式二：克隆仓库后引用
git clone https://github.com/quanmin-lee/bigbang-skill.git
# 在 CLAUDE.md 中加入 skill 路径引用
```

## 快速开始

### 规划阶段 — create-plan

```
/bigbang create-plan <需求描述>
```

启动多角色规划流水线：
1. **架构师** — 评估架构健康度，标注最小主链
2. **策划师** — 分析任务依赖，规划并发批次
3. **测试工程师** — 编写 TDD 验收边界
4. **审查员** — 挑刺审查，决定迭代或终止

产出：`ARCH.md` + `EXECUTION_PLAN.md` + `TEST_BOUNDARIES.md` + `REVIEW_COMMENTS.md` → `PLAN.md`

### 执行阶段 — fast-move

```
/bigbang fast-move --plan PLAN.md
```

按规划并发执行，每个任务走 TDD 流程（RED → GREEN → REFACTOR），自动 git commit。

## 命令

| 命令 | 用途 |
|------|------|
| `/bigbang help` | 显示帮助 |
| `/bigbang create-plan <需求>` | 规划流水线 |
| `/bigbang fast-move --plan <PATH>` | 并发执行 |

## 核心原则

- **最小主链优先** — 先打通端到端通路，再逐步完善
- **TDD 强制** — 所有代码走 RED → GREEN → REFACTOR
- **Git 纪律** — `feat/fix/test/refactor/chore` 规范提交
- **会话内持久化** — 角色 subagent 跨调用复用

## 文件结构

```
skills/bigbang/
├── SKILL.md                    # 入口路由 + 工作流说明
├── prompts/
│   ├── architect.md            # 架构师 prompt
│   ├── planner.md              # 策划师 prompt
│   ├── tester.md               # 测试工程师 prompt
│   ├── reviewer.md             # 审查员 prompt
│   ├── dev-lead.md             # 开发工程师 prompt
│   └── executor.md             # 执行器 prompt
└── .claude/agents/             # 角色 agent 定义
```

## 评估

3 轮迭代评估，with-skill 18/18 断言 100% 通过。
详见 `bigbang-workspace/`。
