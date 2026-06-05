# Requirements Analysis: Excel Aggregate CLI Tool

## 1. Problem Statement

需要构建一个 Python CLI 工具，能够读取 Excel (.xlsx) 文件，按指定列对数值数据进行分组汇总，并将汇总结果输出为 CSV 格式的报表。

## 2. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR1 | 读取 .xlsx 格式的 Excel 文件作为输入 | P0 |
| FR2 | 支持通过 `--column` 参数指定分组的列名 | P0 |
| FR3 | 对指定列以外的数值列自动进行汇总（sum） | P0 |
| FR4 | 将汇总结果输出为 CSV 格式文件 | P0 |
| FR5 | 提供 `--input` 参数指定输入文件路径 | P0 |
| FR6 | 提供 `--output` 参数指定输出文件路径 | P0 |

## 3. Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR1 | 脚本应能处理常见大小的 Excel 文件（< 100MB） | P1 |
| NFR2 | 提供清晰的错误提示（文件不存在、列不存在、非数值列等） | P1 |
| NFR3 | 支持 `--help` 查看使用说明 | P1 |
| NFR4 | 最小外部依赖，仅依赖必要库 | P2 |

## 4. Usage Example

```bash
python aggregate.py --input sales.xlsx --column region --output summary.csv
```

输入 `sales.xlsx`:

| region | product | revenue | cost | quantity |
|--------|---------|---------|------|----------|
| North  | A       | 1000    | 500  | 10       |
| North  | B       | 2000    | 800  | 15       |
| South  | A       | 1500    | 700  | 12       |
| South  | C       | 3000    | 1200 | 20       |

输出 `summary.csv`:

| region | revenue | cost | quantity |
|--------|---------|------|----------|
| North  | 3000    | 1300 | 25       |
| South  | 4500    | 1900 | 32       |

## 5. Boundary Cases

- 输入文件不存在 => 报错退出
- 指定的 `--column` 列不存在 => 报错退出
- 指定列没有重复值 => 每行独立成组，结果与原表数值汇总等价
- 所有数值列值为空 => 结果中该组对应值为 0 或 NaN
- 文件包含多个 sheet => 默认只读取第一个 sheet
- 指定列包含空值 => 空值作为独立分组处理
