# 架构评估报告

## 需求理解

开发一个 Python CLI 工具，接收三个参数（--input, --column, --output），读取 Excel (.xlsx) 文件，按指定列汇总（聚合）数值数据，输出汇总结果至 CSV 文件。

这是一个**全新项目**（greenfield），无需适配或重构现有代码，架构评估聚焦于设计方案的质量和可执行性。

## 项目概览

- **项目类型**: 纯 Python CLI 工具，无长期运行服务
- **技术栈**:
  - Python 3.10+
  - `openpyxl` 或 `pandas` + `openpyxl` 引擎 — 读取 .xlsx
  - `argparse` 或 `click` — CLI 参数解析
  - `csv` 标准库 — 输出 CSV
- **数据流**: `Excel 文件 → 读取 → 按列分组聚合 → CSV 输出`
- **生命周期**: 一次性运行，执行完毕即退出

## 维度评分

| 维度 | 评分 | 依据 |
|------|------|------|
| 架构健康度 | 5/5 | 新项目无历史包袱，可自由设计清晰的数据流和模块边界。输入→处理→输出三段式结构天然解耦。 |
| 可维护性 | 5/5 | 功能单一明确，函数数量可控制在 3-5 个以内，职责清晰。无需复杂的类层次，模块化天然良好。 |
| AI 可读性 | 5/5 | 极简接口设计，三个参数名自描述（`--input`, `--column`, `--output`）。函数命名可做到见名知意。 |
| 模块化 | 4/5 | 天然三段式：read → aggregate → write。扣 1 分是因为文件级抽象取决于实现方式——如果用 pandas 一行搞定，模块化反而弱；需要主动拆分函数。 |
| 可测试性 | 5/5 | 纯函数式数据转换，无外部状态，无数据库/网络依赖。Excel 读取和 CSV 写入可通过临时文件完美隔离。 |

## 最小主链（V1）

| 改动点 | 涉及文件 | 风险 | 说明 |
|--------|---------|------|------|
| 项目骨架 | `pyproject.toml` / `requirements.txt` | 低 | 标准 Python 项目初始化，无风险 |
| CLI 入口 | `cli.py` | 低 | argparse 三个参数，标准做法 |
| Excel 读取模块 | `reader.py` | 中 | openpyxl API 熟悉度决定工作量；需要考虑 .xlsx 多 sheet、表头行、空值处理 |
| 聚合逻辑 | `aggregator.py` | 低 | 按列 groupby + sum/mean，纯数据逻辑 |
| CSV 输出 | `writer.py` | 低 | csv.writer 标准用法 |
| 主流程编排 | `main.py` 或入口模块 | 低 | 串联 read → aggregate → write |

## V2+ 建议

- `--agg` 参数选择聚合方式（sum/mean/count/min/max），V1 默认 sum
- `--sheet` 参数指定工作表名，V1 默认第一个 sheet
- `--format` 输出格式选项（CSV vs JSON vs 终端表格）
- `--verbose` 详细日志模式
- 多列分组支持（`--group-by col1 col2`）
- 全局异常捕获与用户友好错误提示
- `setup.py` 或打包为 pip 可安装包
- 类型注解（stub 或完整 typing）

## 风险与注意事项

- **Excel 兼容性**: `.xlsx` 格式支持良好，但 `.xls`（旧格式）需额外依赖（xlrd）。明确约定只支持 `.xlsx`。
- **大文件内存**: 如 Excel 文件极大（数十万行），需考虑分块读取或改用 `pandas.read_excel(chunksize=...)`。V1 不做优化，标注为已知限制。
- **列名匹配**: `--column` 匹配列名时区分大小写？V1 约定精确匹配，V2 加模糊/忽略大小写。
- **非数值容错**: 指定列包含非数值数据时，V1 默认 skip + warning，V2 加 `--strict` 模式。
