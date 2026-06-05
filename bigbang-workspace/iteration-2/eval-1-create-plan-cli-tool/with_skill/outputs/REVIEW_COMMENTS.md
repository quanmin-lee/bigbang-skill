# 审查意见 - 第 1 轮

## 架构评估

- ✅ 模块划分清晰，src/cli.py / reader.py / summarizer.py / writer.py 关注点分离合理
- ✅ 建议了 pandas 和 openpyxl 两种方案并给出 trade-off 对比
- ✅ V1 标注了完整的 6 个改动点及风险等级
- ✅ V2+ 建议全面，覆盖了多列、多聚合函数、多 sheet、正则匹配等合理扩展方向
- ⚠️ 建议：reader.py 的接口契约应明确——返回原始的 pandas DataFrame 还是已经按列筛选后的 Series？建议明确约定 read_excel(path) -> DataFrame（全量），然后由 summarizer 负责列提取。这样 reader 职责单一。
- ⚠️ 建议：未提及 `--column` 支持列号（int）作为备选输入方式。Excel 用户常使用列号（A/B/C 或 1/2/3）。

## 执行计划

- ✅ 任务分解粒度合理，8 个任务各自职责清晰
- ✅ 批次规划合理，Batch 1 完成基础设施，Batch 2 完成主链，Batch 3 测试覆盖
- ✅ 依赖图清晰，T3→T4 的先后关系正确
- ✅ 标注了 contract-first 建议，降低集成风险
- ❌ **问题**: T4（数值汇总模块）被放在 Batch 2，但它的前置依赖只有 T3（Excel 读取）。T3 在 Batch 1 中，意味着 T4 完全可以和 T2/T5 一起并行，只要 T3 先完成。建议将 T4 移至 Batch 1，标注为依赖 T3。
- ⚠️ 建议: T2（CLI 参数解析）与 T5（CSV 输出模块）完全独立，可在 Batch 1 中标注 [parallel]。

## 测试边界

- ✅ P0 测试场景覆盖全面，每个模块都有正常路径 + 错误路径测试
- ✅ 测试场景表清晰，输入/预期输出/优先级三列齐全
- ✅ Mock 策略合理（pandas.testing 模拟 DataFrame，tempfile 处理输出）
- ✅ 测试执行顺序标注了模块间依赖关系
- ⚠️ 建议: T2 测试中 `--help` 场景应同时 assert 帮助字符串包含 "--input"、"--column"、"--output" 关键词，确保帮助信息完整。
- ⚠️ 建议: T5 测试缺少对 `index=False` 的验证——如果 to_csv 没有 index=False，输出 CSV 会多一列行号。应添加该验收条件。
- ⚠️ 建议: T4 的测试场景中，"非数值列"应细分为：全为非数值（应该报错）vs 混合类型列（只汇总数值，忽略非数值）。两种行为需要区分测试。

## 综合判定

- **状态**: ⚠️ 需要第 2 轮
- **裁决说明**: 执行计划中存在一个批次划分问题（T4 不应在 Batch 2），以及若干测试细节补充。修正后可终止。

## 本轮已解决问题

- 无（首轮审查，无先前问题）

## 本轮遗留问题（修复后即可终止）

1. **执行计划**: T4 应移至 Batch 1（依赖 T3，但与 T2/T5 并列），调整批次规划
2. **测试边界**: T2 的 --help 场景应 assert 帮助文本；T5 应验证 index=False；T4 应区分全非数值列 vs 混合类型列
3. **架构**: reader.py 接口契约应明确；--column 应说明是否支持列号

---

## 合并建议

### 架构决策（来自 ARCH.md）

1. 采用四模块划分：cli.py（入口）、reader.py（读取）、summarizer.py（汇总）、writer.py（输出），关注点分离
2. V1 使用 pandas + openpyxl 快速实现，V2+ 考虑 openpyxl 瘦身
3. reader.py 接口约定为 `read_excel(path) -> DataFrame`（返回全量数据），列提取由 summarizer 负责
4. --column 参数同时支持列名（str）和列号（int）

### 执行计划（来自 EXECUTION_PLAN.md，修正后）

**Batch 1 [CRITICAL_PATH]**: T1 项目初始化 → [T3 Excel 读取, T4 数值汇总]（T4 依赖 T3）→ [T2 CLI 参数解析 [parallel], T5 CSV 输出 [parallel]]
**Batch 2 [CRITICAL_PATH]**: T6 CLI 主流程集成
**Batch 3 [ENHANCEMENT]**: T7 单元测试 [parallel], T8 集成测试 [parallel]

### 测试策略（来自 TEST_BOUNDARIES.md）

- 测试框架: pytest
- Mock 策略: 模拟 DataFrame 避免真实文件依赖，monkeypatch 模拟 CLI 参数
- P0 必须覆盖: 正常数据流、文件不存在、列不存在、参数缺少
- T5 测试需验证 `index=False` 不会产生多余行号列
- T4 测试需区分全非数值列（报错）与混合类型列（忽略非数值列）

### 输入/输出契约

- reader.read_excel(path: str) -> pandas.DataFrame（全量数据，不筛选列）
- summarizer.summarize(df: DataFrame, column: str|int) -> DataFrame（聚合结果）
- writer.write_csv(df: DataFrame, path: str) -> None
- cli.parse_args(argv: list[str]) -> argparse.Namespace
- cli.main() -> int（退出码）

### 关键风险提醒

1. **contract-first**: T3 和 T4 必须先在接口层面上达成一致（read_excel 返回格式），再各自实现，否则集成阶段会阻塞
2. **pandas 依赖**: V1 强依赖 pandas + openpyxl，在 CI 或部署环境中需确保这两个包已安装
3. **Windows 路径兼容**: 所有文件路径操作必须使用 pathlib，避免硬编码路径分隔符
