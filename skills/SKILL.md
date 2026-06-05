---
name: bigbang
description: "Multi-role project workflow orchestrator with two modes: '/bigbang create-plan' runs a planning pipeline (architect, planner, tester, reviewer) to produce structured plans; '/bigbang fast-move' executes those plans via concurrent TDD sub-agents. Trigger for: multi-step project planning, architecture evaluation and breakdown, critical-path analysis, structured review before implementation, refactoring with planning, or any request involving '先规划再执行'. NOT for: single-file edits, one-off code generation, bug fixing, deployment, CI/CD config, documentation, data analysis, diagram drawing, code translation, or PR review (use dedicated skills instead). When unsure, do NOT trigger."
---

# BigBang Skill

轻量级工具包，两大命令：

```
/bigbang help                          → 显示帮助
/bigbang create-plan <需求>            → 多角色规划流水线（架构师→策划→测试→审查）
/bigbang fast-move --plan <PLAN.md>    → 最小主链并发执行（TDD → 实现 → 提交）
```

## 命令路由

```
bigbang help / bigbang ? / 仅输入 /bigbang
  → 显示本帮助信息（命令列表 + 简要说明）

bigbang create-plan <需求>
  → 走 create-plan 流水线

bigbang fast-move --plan <PLAN.md>
  → 走 fast-move 执行流程

输入不匹配以上规则
  → 显示帮助信息
```

## 使用流程

create-plan 和 fast-move 是**先后衔接**的两个阶段：
1. 先用 `create-plan` 产出 PLAN.md（架构评估 + 执行计划 + 测试策略）
2. 再用 `fast-move --plan PLAN.md` 执行
3. 也可以直接 `fast-move --plan` 传入手写的 plan

---

## 关键原则

### 最小主链优先
任何 Plan 都应包含完整的长期愿景，但必须明确标注 V1（最小可运行主链）与 V2+（后续完善）的边界。第一版必须是一个能跑通的最短端到端通路。拒绝"全部改完再一次性大测试"的模式。

### TDD 强制
所有代码执行必须走 RED → GREEN → REFACTOR：
- RED: 写一个会失败的测试
- GREEN: 写最少代码让测试通过 → **git commit**
- REFACTOR: 重构优化 → **git commit**
- RED 阶段不提交

### Git 纪律
- 格式: `<type>: <简短描述>`
- 类型: feat, fix, test, refactor, chore
- subagent 自主提交，不需要批准。开发工程师在批次间检查时发现风格不对可驳回
- 禁止 `--no-verify`，禁止 `--amend`
- **每次 GREEN 提交一次、REFACTOR 提交一次，分开提交，不要合并在一条消息里**

### 会话内持久化
角色 subagent 通过 Agent 工具的 `name` 参数实现会话内复用。首次调用传 `name="architect"` 创建；同一会话中再次向 `name="architect"` 发消息会继续已有会话（如果有），否则创建新的。这是一种"尽力复用"——不需要预先检查 name 是否被占用。

**不跨会话**：每次新的 Claude Code 会话都需要重新创建角色 subagent。

---

## 工具一: create-plan

**用户输入**: `/bigbang create-plan <需求描述>`

### 固定角色（全部持久存活于会话中）

| 角色 | 职责 | 输出 |
|------|------|------|
| `architect` (架构师) | 评估架构健康度、可维护性、AI 可读性、模块化 | `ARCH.md` |
| `planner` (策划师) | 规划并发执行流程、最小主链分组、任务依赖 | `EXECUTION_PLAN.md` |
| `tester` (测试工程师) | 编写 TDD 测试验收边界 | `TEST_BOUNDARIES.md` |
| `reviewer` (审查员) | 对架构评估、执行计划、测试边界进行挑刺审查 | `REVIEW_COMMENTS.md` |

### 启动协作流程

#### Subagent Prompt 拼接规则

每个角色的 prompt = **角色模板文件** + **用户需求 + 上下文**。具体规则:

1. 读取对应角色的 prompt 模板文件（`prompts/<role>.md`）
2. 在模板内容后**追加**以下上下文：
   ```
   ---
   ## 本轮输入
   - 用户需求: <原始用户输入>
   - 项目根目录: <pwd>
   - 当前迭代轮次: 第 N 轮
   </如果有上一次的审查意见，追加>
   - 上一轮审查意见: REVIEW_COMMENTS.md 内容
   ```
3. 拼接后的完整文本作为 Agent 工具的 `prompt` 参数

不要在 prompt 模板中硬写需求——模板是骨架，需求由 Lead Agent 在调用时注入。

#### 首次调用 & 复用规则

**创建 subagent**：使用 Agent 工具，`name` 设为角色英文名（architect/planner/tester/reviewer），`prompt` 为拼接后的完整指令。

**复用 subagent**：直接使用 Agent 工具的 `name` 参数向已有角色发消息。如果该 name 当前没有活跃会话，会创建一个新的；如果有，会继续已有会话。这是一种"尽力复用"机制——无法预先检查 name 是否被占用，直接发即可。

#### 并发启动（❗ 关键）

第 1-3 步（架构师、策划师、测试工程师）不存在数据依赖，**必须在同一条消息中发送多个 Agent 工具调用**来实现并发：

```
同一条消息:
  Agent(description="architect", name="architect", prompt=拼接后的架构师指令)
  Agent(description="planner", name="planner", prompt=拼接后的策划师指令)
  Agent(description="tester", name="tester", prompt=拼接后的测试工程师指令)
```

等待三者都完成后，再启动审查员。审查员依赖前三者的产出。

**降级策略**: 如果 Agent 工具不可用（嵌套 subagent 场景），Lead Agent 应退化为由自己直接扮演各角色，**按角色分段输出同一份文件**（如先以架构师视角写 ARCH.md，再以策划师视角写 EXECUTION_PLAN.md），最后以审查员视角审查。角色切换时注明当前扮演的角色即可。

#### 执行流水线

```
第 N 轮（并发启动架构师 + 策划师 + 测试）:
  1. architect → ARCH.md
  2. planner → EXECUTION_PLAN.md
  3. tester → TEST_BOUNDARIES.md
  --- 等待三者完成 ---
  4. reviewer → REVIEW_COMMENTS.md（审查前三者产出）
     审查员判断是否需要下一轮
```

终止条件:
- 审查员连续两轮无"重大修改意见"（只改措辞/格式等非实质性内容）
- 或达到 5 轮硬性上限

**精准回退**: 当审查员判定需要第 N+1 轮时，不要盲目重跑所有角色。审查意见会指出哪个角色的产出有问题（如"架构评估 OK，测试边界缺少 P0 覆盖率"）。Lead Agent 据此**只重跑有问题的角色**，已通过的角色及其产出不重跑。

最终产出: Lead Agent 基于审查员的合并建议，写入 `PLAN.md`

审查员在 `REVIEW_COMMENTS.md` 末尾附加 `## 合并建议` 章节提供合并框架，**Lead Agent 负责**将审查员的建议转换为最终的 `PLAN.md`。职责分离：审查员判断质量，Lead Agent 执行组装。

**合并验证**: 写入 PLAN.md 后，Lead Agent 快速验证是否完整包含了 ARCH.md、EXECUTION_PLAN.md、TEST_BOUNDARIES.md 中的核心内容（架构决策、任务分解、测试策略）。如果发现有内容缺失，退回审查员补充合并建议。

#### 完成后向用户展示

PLAN.md 写入成功后，向用户展示简洁摘要：

```
✅ create-plan 完成
- 架构评估: <核心结论>
- 执行计划: N 个任务，分 X 个批次
- 测试策略: P0 测试覆盖 <关键路径>
- 审查迭代: 共 N 轮
- 完整计划: PLAN.md

下一步: 运行 /bigbang fast-move --plan PLAN.md 进入执行阶段。
```

---

## 工具二: fast-move

**用户输入**: `/bigbang fast-move --plan <PLAN.md>`

如果用户输入 `/bigbang fast-move` 但没有 `--plan` 参数，提示用户提供 plan 文件路径：`请指定 plan 文件：/bigbang fast-move --plan <path>`。

### 角色

| 角色 | 职责 | 输出 |
|------|------|------|
| `dev-lead` (开发工程师) | 规划/确认最小主链任务清单 | `CRITICAL_PATH.md` |
| 复用 `planner` (策划师) | 分配并发批次和依赖关系 | 确认/更新 `EXECUTION_PLAN.md` |

### 执行流程

1. **开发工程师**产出/确认 `CRITICAL_PATH.md`（最小主链任务清单）
   - 如果 PLAN.md 来自 `create-plan`（已有 EXECUTION_PLAN.md），只做确认/微调
   - 如果 PLAN.md 是手写的，开发工程师负责从零规划最小主链

2. **策划师**产出/确认 `EXECUTION_PLAN.md`（批次规划 + 依赖关系）

3. **按批次执行**:
   - 第一批: `[CRITICAL_PATH]` 任务
   - 后续批: `[ENHANCEMENT]` 任务

   每个任务由独立的匿名 **executor subagent** 执行。Executor 的 prompt 构造规则（Lead Agent 执行）:

   ```
   读取 prompts/executor.md 作为模板
   从 CRITICAL_PATH.md 中读取当前任务 Tn 的详细信息
   拼装 executor prompt = executor.md 模板 + 以下任务上下文:
     ---
     ## 任务详情
     - 任务ID: Tn
     - 任务描述: <来自 CRITICAL_PATH.md>
     - 输入: <来自 CRITICAL_PATH.md 的输入/输出契约>
     - 输出: <来自 CRITICAL_PATH.md 的输入/输出契约>
     - 验收条件: <来自 CRITICAL_PATH.md 的验收条件>
     - 实现指引: <来自 CRITICAL_PATH.md 的实现指引>
     - 项目根目录: <pwd>
     - 前置产出: <如果依赖其他 executor 的输出，说明>
   ```

   每个 executor **只领一个任务**，完成后立即报告。

   同批次内无依赖关系的任务，使用并发 subagent 执行（同一条消息多个 Agent call）。

4. **批次间检查**:
   - 开发工程师 + 策划师检查本批次产出
   - 验证质量
   - 调整下一批次计划

5. **异常处理**:
   - Executor 失败超过 N 次 → 上报开发工程师介入决策

6. **全部完成后**:
   - 验证最小主链跑通
   - 向用户展示简洁摘要:
     ```
     ✅ fast-move 完成
     - 执行批次数: N 批
     - 总任务数: N（通过 N / 失败 N）
     - 提交次数: N
     - 测试结果: X/Y 通过
     - 最终状态: ✅ 成功

     项目可用。关键文件和测试路径已就绪。
     ```

---

## 工作指引：subagent 间通信

角色 subagent 通过**文件系统**进行通信：
1. 每个角色将其产出写入约定的路径（如 `ARCH.md`、`EXECUTION_PLAN.md`）
2. 后续角色读取这些文件作为输入
3. 最终产物 `PLAN.md` 包含所有子产物的汇总

Executor 之间不直接通信，每个 executor 独立领走一个任务，通过约定输入/输出路径协作。

---

## 文件加载指引

本 skill 的 prompts/ 目录包含每个角色的完整 prompt 模板。当需要启动某个角色 subagent 时，读取对应 prompt 文件内容，作为 Agent 工具的 prompt 参数传入。

本 skill 的 `.claude/agents/` 目录定义了每个角色的 agent 配置（名称、描述、工具列表），**仅供 Lead Agent 参考**（了解各角色的工具集等配置信息）。实际的 subagent 调用由 Lead Agent 通过 Agent 工具直接完成，而非通过 agent 文件注册。

