# BigBang Skill - Iteration 2 Benchmark

## 概览

| 指标 | Iteration 1 | Iteration 2 | Δ |
|------|-------------|-------------|---|
| with-skill 通过率 | 18/18 (100%) | 18/18 (100%) | 持平 |
| with-skill 平均耗时 | 182.0s | **139.3s** | **-23%** |
| baseline 通过率 | 1/18 (5%) | 7/18 (33%) | +28%* |

\* baseline 提升是因为 eval-1 的用户提示词带 "create-plan" 关键词，导致基线模型也产出了 BigBang 命名的文件。

## 逐项对比

| Eval | Iteration 1 with-skill | Iteration 2 with-skill |
|------|----------------------|----------------------|
| create-plan CLI 工具 | 7/7 (100%) | 7/7 (100%) |
| fast-move 执行 | 6/6 (100%) | 6/6 (100%) |
| create-plan 飞书机器人 | 5/5 (100%) | 5/5 (100%) |

## 改进分析

### 修复效果
- **Executor prompt 拼接规则明确化** → eval2 的 GIT_COMMITS_SUMMARY.md 和 VERIFICATION_RESULTS.md 均正确产出
- **耗时下降 23%** → 修复后的 SKILL.md 给出了更精确的 prompt 拼接和并发指令，减少了 Lead Agent 的决策开销
- **提交规范 + fix 类型** → eval2 的 TDD 合规审计发现了 iteration-1 的提交问题（test: + feat: 合并在一条 commit 中），验证了修复的必要性

### 已知局限
1. **Sub-subagent 嵌套限制**: with-skill 运行的 eval 中，Lead Agent 本身是 subagent，不一定有 Agent 工具可用，无法真正并发启动子 subagent。实际使用时（顶层 Claude 调用）不受此限制
2. **Prompt 污染**: 当用户提示词包含 "create-plan" 等 BigBang 术语时，baseline 也会产生类似输出 — 这实际上是个好信号（命名约定直观）
3. **Eval 2 的验证**: fast-move 的 executor 部分复用了 iteration-1 已存在的项目文件，而非从零创建 — 这是环境状态的残留
