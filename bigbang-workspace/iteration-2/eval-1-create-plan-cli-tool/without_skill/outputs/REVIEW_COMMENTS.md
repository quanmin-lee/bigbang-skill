# 审查意见 - 第 1 轮

## 架构评估 (ARCH.md)

- ✅ **需求理解准确**：对 CLI 工具的三个参数和功能的描述完全正确
- ✅ **技术选型合理**：`argparse` + `openpyxl` + `csv` 是最小依赖组合，仅 openpyxl 一个外部包
- ✅ **模块化评分恰当**：三个函数各司其职、可独立测试，5 分可测试性合理
- ⚠️ **V1 边界可以更清晰**：ARCH.md 把 V1 定义为"项目目录 + 核心逻辑 + 测试"，但没有明确标注哪些功能属于 V1 / 哪些属于 V2+。建议在 V1 表格中明确标注"不做分组汇总"、"不做多列支持"
- ✅ **风险识别全面**：大文件性能、空列处理、CSV 编码、路径不存在，四个风险点都覆盖了
- ⚠️ **目录位置建议**：`tools/excel-summarizer/` 可以，但也可以考虑更扁平的 `tools/excel_summarizer/`（用下划线而非连字符），更符合 Python 包命名惯例

## 执行计划 (EXECUTION_PLAN.md)

- ✅ **任务分解粒度合理**：T1-T4 四个任务，每个任务都能在 10-30 分钟内完成
- ✅ **依赖分析正确**：T2 和 T3 确实可并发，T4 依赖前两者
- ✅ **批次分组合理**：Batch 1 全部为 [CRITICAL_PATH]，V2+ 推迟到 Batch 2
- ⚠️ **T2/T3 并发风险未被充分缓解**：计划中提到了"T3 基于 stub 写测试"的思路，但没有具体落地。建议在 T2 中先产出函数签名 stub（空的函数定义 + docstring），T3 基于 stub 写测试，然后再填充实现。——不过这在严格并发中做不到，建议要么把 T2 拆分为 T2a (stub) + T2b (实现)，T2a 与 T3 并发；要么 T2 和 T3 串行（T2→T3），接受更短的执行时间
- ✅ **V2+ 任务规划合理**：多列汇总、分组汇总、错误处理，三个增强功能优先级正确

## 测试边界 (TEST_BOUNDARIES.md)

- ✅ **测试覆盖全面**：正常路径、混合类型、空列、列不存在、文件不存在，五个场景都覆盖了
- ✅ **P0/P1 优先级标注合理**：核心路径全部标 P0，边界条件标 P1
- ✅ **测试策略清晰**：单元测试用 mock、集成测试用真实文件，区分明确
- ✅ **测试数据动态生成**：用 `openpyxl.Workbook()` 在 `tmp_path` 创建，不提交二进制文件，很合理
- ⚠️ **缺少一个测试场景**：列中有**负数**的情况。虽然 sum() 自然支持，但这是一个边界值测试
- ⚠️ **CSV 编码**：TEST_BOUNDARIES.md 提到用 `utf-8-sig` 写入 CSV，但这是 V1 实现的细节。合理，但不是测试需直接关注的点，暂不扣分

## 综合判定

- **状态**: ⚠️ **需要第 2 轮**（1 个需要澄清的问题 + 1 个可优化点）

### 需要下一轮解决的问题（优先级排序）

1. **T2/T3 并发策略不够明确**：目前 EXECUTION_PLAN.md 将 T2 和 T3 标注为 [parallel] 但未解决"测试需要已知函数签名"的矛盾。需要决定：是拆分 T1/T2/T3 为 T1→T2a+T3→T2b 的流水线，还是改为串行。这个问题会直接影响 fast-move 阶段的实际执行效率。
2. **V1/V2+ 边界可以更清晰**：ARCH.md 的 V1 表格应补充"不做"列表（not doing），明确哪些功能被推迟到 V2+。

### 当前轮已解决问题（首轮无历史）

无。

## 合并建议

### 架构决策（来自 ARCH.md）

1. **独立模块**：新工具放在 `tools/excel-summarizer/`（或用下划线 `excel_summarizer`），不侵入现有业务代码
2. **最小依赖**：仅依赖 `openpyxl` 一个外部包，CLI 框架用 stdlib `argparse`，CSV 输出用 stdlib `csv`
3. **三阶段管道**：读 Excel → 汇总（sum）→ 写 CSV，三个阶段对应三个纯函数
4. **UTF-8 编码**：CSV 使用 `utf-8-sig` 编码以兼容 Excel 直接打开中文 CSV

### 执行计划（来自 EXECUTION_PLAN.md）

**Batch 1 — [CRITICAL_PATH] 主链：**
- T1: 搭建项目骨架（目录、`pyproject.toml`、`requirements.txt`）
- T2: 实现核心 CLI 逻辑（`cli.py` 含参数解析 + 三个处理函数）
- T3: 编写单元测试（`tests/test_cli.py`）
- T4: 端到端集成测试（`tests/test_integration.py`）

**标注说明：** T2 和 T3 原标注为 [parallel] 需根据审查意见确认并发策略。如果改串行，执行顺序为 T1 → T2 → T3 → T4；如果拆分，则为 T1 → T2a (stub) + T3 (test) [parallel] → T2b (impl) → T4。

**Batch 2 — [ENHANCEMENT] 增强：**
- T5: 支持多列汇总
- T6: 支持分组汇总
- T7: 错误处理优化

### 测试策略（来自 TEST_BOUNDARIES.md）

| 优先级 | 测试内容 |
|--------|---------|
| P0 | 正常路径：3行数值 Excel → 正确求和 |
| P0 | 混合类型：列中有非数值 → 忽略非数值，只汇总数值 |
| P0 | 参数解析：--input / --column / --output 三个参数正确解析 |
| P0 | 空列/空工作表 → 返回 0（不崩溃） |
| P1 | 列不存在 → 报错，退出码非 0 |
| P1 | 文件不存在 → 报错，退出码非 0 |
| P1 | 单行数据 → 正确求和 |
| P1 | 负数值 → 正确求和 |

### 输入/输出契约

| 函数 | 输入 | 输出 |
|------|------|------|
| `read_excel(path: str) -> list[dict]` | Excel 文件路径 | 行数据列表，每行为 dict{列名: 值} |
| `summarize_column(data: list[dict], column: str) -> float` | 行数据 + 列名 | 数值总和 |
| `write_csv(data: list[dict], path: str)` | 汇总结果 + 输出路径 | 写入 CSV 文件 |
| `parse_args(argv: list[str]) -> argparse.Namespace` | sys.argv | input/column/output 三个属性 |
| `main()` | 无（读取 sys.argv） | 调用完整管道 |

### 关键风险提醒

1. **openpyxl 环境依赖**：执行前必须 `pip install openpyxl`，否则测试全部失败
2. **T2/T3 并发 or 串行**：这是执行阶段第一个决策点，建议在 fast-move 启动前确定策略
3. **CSV 不含表头**：输出 CSV 是否需要包含原始表头还是只有汇总值？需要确认 —— V1 建议输出两列：`column, sum` 带表头
