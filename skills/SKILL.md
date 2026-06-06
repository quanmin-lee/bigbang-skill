---
name: bigbang
description: "Multi-role project workflow orchestrator with two modes: '/bigbang create-plan' runs a multi-agent planning pipeline with product manager, dynamic role creation, and autonomous consensus iteration; '/bigbang fast-move' executes plans via concurrent TDD sub-agents. Trigger for: multi-step project planning, architecture evaluation and breakdown, critical-path analysis, structured review before implementation, refactoring with planning, or any request involving '先规划再执行'. NOT for: single-file edits, one-off code generation, bug fixing, deployment, CI/CD config, documentation, data analysis, diagram drawing, code translation, or PR review (use dedicated skills instead). When unsure, do NOT trigger."
---

# BigBang Skill

轻量级工具包，三大命令：

```
/bigbang help                          → 显示帮助
/bigbang create-plan <需求>            → 多角色协作规划（PM对需求→动态角色→共识迭代→出PLAN）
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
1. 先用 `create-plan` 产出 PLAN.md（需求文档 → 架构评估 → 执行计划 → 测试策略）
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

### 三层流程

create-plan 现在是一个**三阶段**流程：
1. **Phase 1 — 需求对齐**: PM 与用户对咬需求，用户确认后才进行下一步
2. **Phase 2 — 规划共识**: 所有角色自动规划、评审、迭代，直到全员达成共识，**不需要每轮问用户**
3. **Phase 3 — 通知用户**: 共识达成后，输出 PLAN.md 并向用户展示摘要

### Phase 1: 需求对齐（用户参与）

**必须首先启动产品经理（PM）**。PM 是需求的第一接收人和翻译官。不能跳过此阶段。

1. 读取 `prompts/product-manager.md` 作为 PM 的 prompt 模板
2. 拼接上下文（用户需求原文、项目根目录）
3. 使用 `Agent(name="product-manager", description="产品经理", prompt=拼接后的指令)` 启动 PM
4. PM 会主动和用户对话（追问澄清、确认边界）
5. PM 产出 `PRD.md`（产品需求文档）
6. **等待用户确认 PRD 后**，进入 Phase 2

重要规则：
- **PM 必须先启动，不能跳过需求对齐阶段**
- PM 会话在整个 create-plan 和 fast-move 过程中持久存活，随时可供咨询
- 如果用户通过 PM 修改了需求，PM 更新 PRD.md，其他角色据此调整

### Phase 2: 规划共识（自动迭代，不打扰用户）

#### 2.1 动态创建角色

在 PM 完成 PRD 后，Lead Agent 评估需求的复杂性，决定需要创建哪些角色。

**必须创建的角色**（始终需要）:

| 角色 | 职责 | 输出 |
|------|------|------|
| `architect` (架构师) | 评估架构健康度、可维护性、AI 可读性、模块化 | `ARCH.md` |
| `planner` (策划师) | 规划并发执行流程、最小主链分组、任务依赖 | `EXECUTION_PLAN.md` |
| `tester` (测试工程师) | 编写 TDD 测试验收边界 | `TEST_BOUNDARIES.md` |
| `reviewer` (审查员) | 对整体方案挑刺审查，检查完整性 | `REVIEW_COMMENTS.md` |

**动态创建的角色**（Lead Agent 根据场景自由决定）:
- 示例: `security-expert`（安全专家）、`data-engineer`（数据工程师）、`UX-designer`（交互设计师）、`devops-engineer`（运维工程师）、`domain-expert`（领域专家）等
- **鼓励** Lead Agent 按需创建更多角色。需要什么就创建什么，需求越复杂，角色越丰富
- 创建方式: 使用 `Agent(name="<角色英文名>", description="<角色描述>", prompt=...)` 创建
- 动态角色的 prompt = Lead Agent 根据角色职责自行撰写 + 上下文（PRD、项目根目录）

#### 2.2 Subagent Prompt 拼接规则

每个角色的 prompt = **角色模板文件** + **上下文**:

```
---
## 本轮输入
- 用户需求（原始）: <原始用户输入>
- PRD 摘要: <PRD.md 的核心内容，包括功能清单和边界>
- 项目根目录: <pwd>
- 当前迭代轮次: 第 N 轮
- PM 确认状态: 已确认 / 已更新
</如果有一轮共识反馈，追加>
- 共识反馈汇总: <上轮各角色的评审意见>
```

不要在 prompt 模板中硬写需求——模板是骨架，需求由 Lead Agent 在调用时注入。

#### 2.3 并发启动初稿

第 1 轮，不存在数据依赖的角色**必须在同一条消息中并发启动**:

```
同一条消息:
  Agent(description="架构师", name="architect", prompt=...)
  Agent(description="策划师", name="planner", prompt=...)
  Agent(description="测试工程师", name="tester", prompt=...)
  Agent(description="审查员", name="reviewer", prompt=...)
  Agent(description="<动态角色>", name="<动态角色>", prompt=...)  // 如果有
```

等待所有角色完成初稿。

**降级策略**: 如果 Agent 工具不可用（嵌套 subagent 场景），Lead Agent 退化为由自己直接扮演各角色，按角色分段输出。

#### 2.4 共识评审（核心改进）

**这是最重要的改进**——plan 的通过不再由 reviewer 一人决定，而是**所有角色达成共识**。

每轮共识评审流程:

1. **汇总本轮产出**: Lead Agent 收集所有角色的产出文件
2. **交叉发送评审**: 将各角色产出（角色之间互相不认识，由 Lead Agent 转发）发送给所有角色，每个角色从自己的专业视角评审他人产出:
   - 架构师评审执行计划和测试边界的合理性
   - 策划师评审架构评估与任务分解是否匹配
   - 测试工程师评审架构和执行计划对测试的影响
   - Reviewer 做全面挑刺审查
   - 动态角色评审与自己领域相关的部分
   - **PM 评审所有产出是否偏离 PRD 需求**——这是 PM 的独特视角，不同于技术角色的审查
3. **PM 方向把控与共识投票**: 向 PM 发送消息，PM 检查所有产出是否与 PRD 中的需求一致。**PM 是共识参与者之一，不是旁观者**——如果 PM 认为方案偏离了用户需求，PM 同样给出 ❌，阻塞共识。**当角色间产生冲突时，PM 根据原始需求做出方向性判断**——技术优劣不是裁决依据，用户需求才是
4. **共识判定**: Lead Agent 收集所有角色的意见。
   **Reviewer 负责汇总"各角色风险项清零检查表"**，逐一列出每个角色提出的问题及其解决状态。共识判定的标准如下（按优先级从高到低）:

   | 情况 | 判定 | 说明 |
   |------|------|------|
   | 存在任何 ❌ | ❌ 进入下一轮 | 有角色认为问题必须修正才能共识 |
   | 存在 ⚠️ 且属于实质性风险 | ❌ 进入下一轮 | 即使只是 ⚠️，只要影响可行性/正确性/可维护性，就必须修 |
   | 仅有纯鸡毛蒜皮的 ⚠️ | ✅ 可共识 | 措辞调整、格式美化、排版建议——不影响方案实质 |
   | 全员 ✅ | ✅ 共识达成 | 所有角色的所有问题已清零 |

   **实质性风险的定义**: 所有"有一定可能性会造成问题"的都属于实质性风险。只有"无论如何都不会造成任何实际影响"的才算纯鸡毛蒜皮。

5. **精准回退**: 哪些角色有问题就只重跑哪些角色，已通过的角色不重跑

终止条件:
- **全员共识达成**（所有角色的所有实质性风险已清零，PM 确认 ✅）→ 正常终止
- 或达到 5 轮硬性上限 → Lead Agent 向用户报告哪些角色仍未达成共识及其原因

**关键规则**:
- Lead Agent 在 create-plan 阶段**绝不直接修改规划产出**。如果发现某个角色的产出有问题，反馈给该角色并要求在新一轮中修正
- 整个 Phase 2 **自动迭代，不需要每轮停下来问用户**。PM 手持 PRD 作为方向标，足以在规划阶段把控质量方向
- **共识 ≠ "没有矛盾"**。没有矛盾只意味着意见一致，不代表风险已清零。共识 = **所有角色提出的每一个实质性风险都被解决，无人再持有异议**
- ** reviewer 是"零风险残留"的把控人**。reviewer 的意见是"最终裁定建议"——如果 reviewer 判定仍有未解决的实质性风险，无论 PM 或其他角色怎么看，都必须进入下一轮

#### 2.5 共识确认信号

共识达成后，PM 更新 PRD.md，追加 `## 共识确认` 章节，记录:
- 最终参与的角色列表
- 每个角色的最终状态 ✅
- 关键决策记录（哪些分歧、如何裁决）
- 未尽事宜（留待执行阶段关注）

### Phase 3: 通知用户

1. Reviewer 做最终完整性检查，在 REVIEW_COMMENTS.md 中产出合并建议
2. Lead Agent 基于合并建议写入 `PLAN.md`（包含 PRD 摘要、ARCH.md、EXECUTION_PLAN.md、TEST_BOUNDARIES.md 的核心内容）
3. 展示摘要:

```
✅ create-plan 完成
- 需求对齐: <PRD 核心>
- 参与角色: <所有角色，包括动态创建的>
- 架构评估: <核心结论>
- 执行计划: N 个任务，分 X 个批次
- 测试策略: P0 测试覆盖 <关键路径>
- 共识轮次: 共 N 轮达成全员共识
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
| `planner` (策划师) | **显式触发**，分配并发批次和依赖关系 | 确认/更新 `EXECUTION_PLAN.md` |

### 执行流程

1. **开发工程师**产出/确认 `CRITICAL_PATH.md`（最小主链任务清单）
   - 使用 `Agent(name="dev-lead", ...)` 启动 dev-lead
   - 如果 PLAN.md 来自 create-plan（已有 EXECUTION_PLAN.md），只做确认/微调
   - 如果 PLAN.md 是手写的，开发工程师负责从零规划最小主链
   - 确保 CRITICAL_PATH.md 包含了: 任务 ID、描述、输入/输出契约、验收条件、实现指引

2. **显式触发策划师**（❗ 关键改进）
   - 必须使用 `Agent(name="planner", ...)` 或 SendMessage to="planner" 显式触发 planner
   - 将 CRITICAL_PATH.md 的完整内容通过 prompt 传给 planner
   - Planner 基于 CRITICAL_PATH.md 确认或更新 `EXECUTION_PLAN.md`（批次规划 + 依赖关系）
   - **必须等待策划师完成后再进入下一步**

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
3. 共识评审阶段，Lead Agent 负责将各角色的产出发送给其他角色进行交叉评审
4. 最终产物 `PLAN.md` 包含所有子产物的汇总

Executor 之间不直接通信，每个 executor 独立领走一个任务，通过约定输入/输出路径协作。

---

## 文件加载指引

本 skill 的 prompts/ 目录包含每个角色的完整 prompt 模板。当需要启动某个角色 subagent 时，读取对应 prompt 文件内容，作为 Agent 工具的 prompt 参数传入。

本 skill 的 `.claude/agents/` 目录定义了每个角色的 agent 配置（名称、描述、工具列表），**仅供 Lead Agent 参考**（了解各角色的工具集等配置信息）。实际的 subagent 调用由 Lead Agent 通过 Agent 工具直接完成，而非通过 agent 文件注册。
