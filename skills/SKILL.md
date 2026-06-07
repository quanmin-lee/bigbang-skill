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

### 工程控制论（贯穿全流程）

整个 BigBang 的设计受钱学森《工程控制论》(Engineering Cybernetics, 1954) 的启发。它将软件开发过程视为一个**受控系统**，create-plan 和 fast-move 中的每一个机制都可以用控制论的语言来理解：

| 控制论概念 | 工程含义 | BigBang 中的映射 |
|-----------|---------|----------------|
| **被控对象 (Plant)** | 被控制的系统 | 项目代码库 |
| **期望状态 (Desired State)** | 系统应达到的目标 | PRD 中的需求 |
| **控制器 (Controller)** | 生成控制指令的机制 | create-plan + fast-move 编排流程 |
| **传感器 (Sensor)** | 检测实际状态 | **Checker（验收检查点）** |
| **反馈信号 (Feedback)** | 实际与期望的偏差 | CHECK_REPORT.md |
| **执行器 (Actuator)** | 根据指令修正系统 | Executor / Lead Agent |
| **前馈控制 (Feedforward)** | 提前预防偏差 | 规划/架构/共识评审 |
| **反馈控制 (Feedback)** | 发现偏差后纠正 | Check-it 验收机制 |
| **闭环 (Closed-loop)** | 有反馈回路的控制 | create-plan → fast-move → **check-it** → 调整 |
| **开环 (Open-loop)** | 无反馈回路的控制 | create-plan → fast-move → 无验收（此前的状态）|
| **分层控制 (Hierarchical)** | 不同层级不同控制频率和抽象级别 | PM(战略)→架构师(架构)→策划师(任务)→Executor(实现)→Checker(验收) |

**核心思想**：
- 没有 check-it 的 bigbang 是**开环控制**——做完才知好坏，返工成本极高。加入 check-it 后变成**闭环控制**——每功能落地时检测偏差，及时纠偏
- create-plan 是**前馈控制**——通过规划、评审提前预防问题。check-it 是**反馈控制**——通过验收发现偏差并纠正。两者互补，缺一不可
- **控制与执行分离**：做的人不负责验收，验收的人不参与实现。Checker 独立于 Executor，确保反馈信号客观可信
- **分层控制原则**：Lead Agent 在任何情况下都不得越层干预——不能因为觉得"问题简单"就跳过对应角色的评审（详见 Phase 2 关键规则）。越层控制导致信息丢失，是控制系统失稳的常见原因

### AI 时代的多智能体设计模式

BigBang 的设计吸收了近年 AI 领域的核心研究成果。以下模式解释了为什么多角色协作 + 结构化评审 + 分阶段迭代是当前最可靠的智能体系统架构。

#### 1. 多智能体协作 — Multi-Agent Collaboration（Andrew Ng, 2025）

Andrew Ng 在 2025 年系统总结了四种关键的智能体设计模式（Agentic Design Patterns）：**Reflection（反思）、Tool Use（工具使用）、Planning（规划）、Multi-Agent Collaboration（多智能体协作）**。BigBang 同时实现了其中三种：

| Ng 的设计模式 | BigBang 中的实现 |
|-------------|----------------|
| **Multi-Agent Collaboration** | Phase 2 共识评审——架构师、策划师、测试工程师、Reviewer、PM 交叉评审 |
| **Planning** | Planner 角色做 CPM/TOC 批次规划、识别关键路径 |
| **Reflection** | 共识迭代机制——每轮发现问题→修正→再评审，直到达标 |

**关键发现**：Ng 的研究表明，多智能体协作之所以有效，不是因为单个智能体变强了，而是因为不同视角的交叉验证能过滤个体偏差。一个架构师可能忽略测试可行性，但测试工程师会指出来——这正是 BigBang 多角色评审的本质。

#### 2. 大模型作为裁判 — LLM-as-Judge（2023-2025 系列研究）

一系列研究（GPT-4 as Judge, JudgeLM, PandaLM, LLM-as-a-Judge）发现：**大模型可以有效评估其他大模型的产出，但需要精心设计的评估标准（Rubric）**。核心结论：

| 研究发现 | BigBang 中的应用 |
|---------|----------------|
| 清晰的评分标准 (Rubric) 大幅提升裁判可靠性 | 每个角色有明确的输出模板和评审标准（如 Reviewer 的 ✅/⚠️/❌ + 理由） |
| 多裁判优于单裁判 | 共识评审中**所有角色**都参与评审，不是 Reviewer 一人说了算 |
| 裁判应与被评对象分离（独立性） | **控制与执行分离**：Checker 不参与开发，Reviewer 不参与规划 |
| 结构化输出格式提升裁判一致性 | CHECK_REPORT.md、REVIEW_COMMENTS.md 都有固定格式 |

**具体映射**：
- **Reviewer** = LLM-as-Judge for **方案质量**（计划层面）
- **Checker** = LLM-as-Judge for **验收符合度**（执行层面）
- **共识投票** = Multi-Judge Ensemble（多裁判集成投票）

#### 3. 原则驱动对齐 — Constitutional AI（Anthropic, 2022）

Anthropic 提出的 Constitutional AI 核心思想：**用一套明确的成文原则来引导 AI 行为，比单纯的奖励/惩罚更可靠**。在多智能体系统中，这意味着：

- 每个角色的 prompt 就是它的**宪法**——规定了它能做什么、不能做什么、以什么标准判断
- SKILL.md 本身是多智能体系统的**元宪法**——规定了角色之间的交互规则、共识达成条件、异常处理流程
- 共识机制本质上是一种**多智能体宪法过程**——各角色依据自己的宪法做出判断，通过投票（✅/⚠️/❌）达成集体决策

**在 BigBang 中的体现**：
- Lead Agent 无权推翻角色评审结论——因为"各角色的判断受其宪法保护"
- 共识条件（全员 ✅ / 无 ❌）是宪法的**决议条款**
- "Lead Agent 不得绕过角色评审" 不仅是一个纪律要求，更是宪法原则——越权即违宪

#### 4. 结构化输出与智能体-计算机接口 — ACI（Anthropic, 2024）

Anthropic 的研究表明：**智能体与工具/输入之间的接口设计（Agent-Computer Interface, ACI）直接影响智能体的可靠性**。好的 ACI 设计原则包括：

| ACI 原则 | BigBang 中的实现 |
|---------|----------------|
| 使用结构化格式而非自由文本 | 每个角色的输出有明确的 Markdown 模板（ARCH.md, EXECUTION_PLAN.md 等） |
| 让"可做什么"显式可见 | 每个角色 prompt 明确列出其职责和输出要求 |
| 清晰的边界分隔 | prompt 中的 ---- 分隔线、## 标题层级明确划分信息区域 |
| 输出格式规范降低解析成本 | 表格、检查清单等结构化格式让后续角色和 Lead Agent 都能准确读取 |

**实践意义**：当 Reviewer 产出 REVIEW_COMMENTS.md 时，使用统一的 ❌/⚠️/✅ 标签 + 表格格式，比自由文本描述更容易让其他角色和 Lead Agent 理解和处理。

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

create-plan 现在是一个**三阶段**流程，整体构成 PDCA（Plan-Do-Check-Act）循环中的 Plan 阶段：
1. **Phase 1 — 需求对齐（前馈）**: PM 与用户对咬需求，用户确认后才进行下一步。这是控制论中的**前馈控制**——在问题发生前通过需求澄清来预防偏差
2. **Phase 2 — 规划共识（前馈 + 闭环迭代）**: 所有角色自动规划、评审、迭代，直到全员达成共识，**不需要每轮问用户**。这是多层前馈控制——多个角色从不同视角提前识别风险
3. **Phase 3 — 通知用户**: 共识达成后，输出 PLAN.md 并向用户展示摘要。用户确认后进入 D（Do）阶段

### Phase 1: 需求对齐（用户参与 + 团队反馈）

**必须首先启动产品经理（PM）**。PM 是需求的第一接收人和翻译官。不能跳过此阶段。

1. 读取 `prompts/product-manager.md` 作为 PM 的 prompt 模板
2. 拼接上下文（用户需求原文、项目根目录）
3. 使用 `Agent(name="product-manager", description="产品经理", prompt=拼接后的指令)` 启动 PM
4. PM 会主动和用户对话（追问澄清、确认边界）
5. PM 产出 `PRD.md`（产品需求文档）
6. **PM 做初步影响评估**：PM 查看项目结构，在 PRD.md 中追加 `## 需求影响评估（初步）` 章节（影响范围、改动难度、潜在风险、可行性）。这给用户"团队对这个需求的第一印象"
7. PM 向用户展示 PRD + 影响评估，**一起确认**。用户不只看到"做什么"，还看到"改多少、难不难、值不值得"
8. **用户确认后**，进入 Phase 2

重要规则：
- **PM 必须先启动，不能跳过需求对齐阶段**
- PM 会话在整个 create-plan 和 fast-move 过程中持久存活，随时可供咨询
- 如果用户通过 PM 修改了需求，PM 更新 PRD.md，其他角色据此调整
- PM 的评估是**初步**的，不是最终技术判断。深度分析由架构师在 Phase 2 完成。但 PM 的初步评估让用户在做需求确认时就有全局视野

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

5. **精准回退**: 哪些角色有问题就只重跑哪些角色，已通过的角色不重跑。**不允许 Lead Agent 自己直接修改**——即使修改再简单，也必须由对应角色来改，Lead Agent 只负责传递评审意见

终止条件:
- **全员共识达成**（所有角色的所有实质性风险已清零，PM 确认 ✅）→ 正常终止
- 或达到 5 轮硬性上限 → Lead Agent 向用户报告哪些角色仍未达成共识及其原因

**关键规则**:
- Lead Agent 在 create-plan 阶段**绝不直接修改规划产出**。如果发现某个角色的产出有问题，反馈给该角色并要求在新一轮中修正
- **Lead Agent 不得绕过角色评审**。即使你认为某个修改"很简单，不影响执行"，也必须传回给相关角色评审，而不是自己改完直接问用户要不要跳过。原因：一个修改简单与否不是由 Lead Agent 判断的——架构师可能认为它影响架构方向，PM 可能认为它偏离需求。**Lead Agent 的角色是路由反馈，不是裁决反馈的严重程度**
- **不要问用户"这个简单我直接改了好不好"**。共识迭代是角色之间的博弈，不是 Lead Agent 和用户之间的对话。用户无法判断一个技术修改是否真的简单。你问了就是逼用户做他不该做的技术判断
- 整个 Phase 2 **自动迭代，不需要每轮停下来问用户**。PM 手持 PRD 作为方向标，足以在规划阶段把控质量方向
- **共识 ≠ "没有矛盾"**。没有矛盾只意味着意见一致，不代表风险已清零。共识 = **所有角色提出的每一个实质性风险都被解决，无人再持有异议**
- **reviewer 是"零风险残留"的把控人**。reviewer 的意见是"最终裁定建议"——如果 reviewer 判定仍有未解决的实质性风险，无论 PM 或其他角色怎么看，都必须进入下一轮

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
- 执行计划: N 个任务，分 X 个批次，X 个验收检查点
- 测试策略: P0 测试覆盖 <关键路径>
- 共识轮次: 共 N 轮达成全员共识
- 完整计划: PLAN.md

下一步: 运行 /bigbang fast-move --plan PLAN.md 进入执行阶段。执行中将自动在检查点触发验收（check-it），无需每步手动确认。
```

---

## 工具二: fast-move（PDCA 中的 D → C → A 阶段）

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

4. **验收检查 — Check-it（闭环反馈控制）**
   当本批次触发了 EXECUTION_PLAN.md 中定义的检查点时，必须执行验收检查。这是工程控制论中的**反馈控制**环节——测量实际输出，与期望状态比较，发现偏差，产生修正信号。没有这一步，整个流程就是开环控制，偏差会一路累积到最终验收才被发现。

   **触发条件**：检查 EXECUTION_PLAN.md 的 `## 验收检查点 (Checkpoints)` 表。如果当前批次号匹配表中的"触发批次"，则启动检查。

   **执行检查（PDCA 的 C 阶段）**：
   1. 读取 `prompts/checker.md` 作为 checker 的 prompt 模板
   2. 拼装 checker prompt = checker.md 模板 + 以下上下文:
      ```
      ---
      ## 本轮输入
      - PRD.md: <PRD 内容——这是期望状态>
      - 检查点定义: <从 EXECUTION_PLAN.md 中提取当前批次触发的检查点>
      - 当前批次: Batch N（已完成）
      - 项目根目录: <pwd>
      ```
   3. 使用 `Agent(name="checker", description="验收检查员", prompt=...)` 启动 checker
   4. Checker 执行验证，产出 `CHECK_REPORT.md`（这是反馈信号）

   **结果判定（反馈信号处理 → Act 阶段）**:

   | 判定 | 处理方式（控制动作） |
   |------|-------------------|
   | ✅ 通过 → 偏差为零 | 系统状态良好，继续下一步 |
   | ⚠️ 有偏差但不阻塞 → 偏差在容忍范围内 | 记录偏差趋势，继续下一步。偏差虽小但需跟踪——控制论中"偏差累积效应"可能导致系统逐渐偏离目标 |
   | ❌ 不通过 → 偏差超出控制限 | **暂停**执行（触发负反馈）→ 通知 PM → PM 选择控制策略：A. 微调任务后可继续（局部修正）/ B. 需要重新规划（回到 P 阶段）/ C. 容忍偏差继续（有意识的风险接受） |

   **重要**：
   - check-it 是"验收"不是"验证"。它检查"功能是否满足 PRD 需求"（用户视角），不是"代码是否正确"（那是测试的事）
   - **控制与执行分离**：Checker 与 Executor 是独立角色。做的人不验收，验收的人不实现，确保反馈信号客观可信
   - 这一步让整个 fast-move 从**开环控制**变为**闭环控制**。每一次 check-it 执行，就是一次控制回路闭合

5. **批次间检查**:
   - 开发工程师 + 策划师检查本批次产出
   - 验证质量
   - 调整下一批次计划

6. **异常处理**:
   - Executor 失败超过 N 次 → 上报开发工程师介入决策

7. **全部完成后**:
   - 运行所有未触发的最终验收检查（如有全局检查点）
   - 验证最小主链跑通
   - 向用户展示简洁摘要:

```
✅ fast-move 完成
- 执行批次数: N 批
- 总任务数: N（通过 N / 失败 N）
- 检查点: X/Y 通过
- 已知问题: <如有>
- 提交次数: N
- 测试结果: X/Y 通过
- 最终状态: ✅ 成功 / ⚠️ 有未解决问题
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
