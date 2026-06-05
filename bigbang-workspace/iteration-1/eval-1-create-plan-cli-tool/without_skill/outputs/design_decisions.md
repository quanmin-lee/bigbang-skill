# Design Decisions: Excel Aggregate CLI Tool

## Decision 1: 单文件 vs 多模块

**Context:** 是否需要将代码拆分为多个文件/包。

**Options:**
- A. 单文件 `aggregate.py`（所有逻辑集中）
- B. 多模块包结构（`src/`, `cli.py`, `core.py` 等）

**Decision:** A. 单文件

**Rationale:** 工具功能单一（~50 行核心逻辑），单文件即插即用，无需 pip install -e，复制即用。多模块对于这个规模过度设计。

## Decision 2: pandas + openpyxl vs openpyxl 裸写

**Context:** 如何读取 Excel 文件并进行分组汇总。

**Options:**
- A. pandas.read_excel + groupby + sum
- B. openpyxl 手动解析行列 + 字典聚合

**Decision:** A. pandas + openpyxl

**Rationale:** pandas 的 groupby 是声明式 API，5 行代码完成读取 + 聚合 + 输出。手动 openpyxl 需要 30+ 行且容易出错。pandas 是 Python 数据处理的事实标准，团队熟悉度高。

**Tradeoff:** 依赖体积增加（~10MB），但对于数据处理工具这是可接受的。

## Decision 3: 必选参数 vs 交互式提示

**Context:** 用户未提供参数时的行为。

**Options:**
- A. argparse 设 `required=True`，缺失时报错退出
- B. 交互式 input() 提示用户输入

**Decision:** A. 必选参数 + --help

**Rationale:** CLI 工具应遵循 Unix 传统：静默执行或报错退出，不阻塞等待输入。适合脚本管道和自动化场景。--help 提供完整使用说明。

## Decision 4: numeric_only=True vs 手动筛选数值列

**Context:** groupby sum 时如何处理非数值列。

**Options:**
- A. `groupby(col).sum(numeric_only=True)`
- B. 手动 `select_dtypes(include='number')` + 按列聚合

**Decision:** A. numeric_only=True

**Rationale:** pandas 内置参数，语义明确，一行搞定。无需手动筛选列。

## Decision 5: utf-8-sig 编码

**Context:** CSV 输出编码选择。

**Options:**
- A. utf-8-sig（带 BOM）
- B. utf-8（无 BOM）
- C. gbk

**Decision:** A. utf-8-sig

**Rationale:** 用户大概率会用 Excel 打开 CSV 查看结果。utf-8-sig 的 BOM 让 Excel 能正确识别 UTF-8 编码的中文内容，避免乱码。标准 UTF-8 在 Excel 中常出现中文乱码。
