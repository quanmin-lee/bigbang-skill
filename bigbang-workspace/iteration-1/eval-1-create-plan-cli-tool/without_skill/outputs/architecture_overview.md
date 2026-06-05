# Architecture Overview: Excel Aggregate CLI Tool

## 1. Architecture Style

单文件 CLI 工具架构，遵循 Unix 哲学：做好一件事。

```
User Input (CLI args)
       |
       v
  parse_args()      -- argparse: --input, --column, --output
       |
       v
  validate_args()   -- 文件存在性检查、列名校验
       |
       v
  read_excel()      -- pandas.read_excel，读取第一个 sheet
       |
       v
  aggregate()       -- groupby(column) + sum(numeric_only=True)
       |
       v
  write_csv()       -- to_csv(index=False)
       |
       v
  Output CSV File
```

## 2. Module Structure

```
aggregate.py                  # 主入口，所有逻辑集中在一个文件
requirements.txt              # 依赖清单
```

单文件设计的原因：
- 工具功能单一（~50 行核心逻辑），无需分包
- 易于分发和部署，复制单个文件即可使用
- 便于用户阅读和修改

## 3. Component Breakdown

### 3.1 CLI Argument Parser (`parse_args`)

- 使用 `argparse`（Python 标准库）
- 定义三个必选参数：`--input`, `--column`, `--output`
- 自动生成 `--help` 文档

### 3.2 Validator (`validate_args`)

- 输入文件存在性校验（`os.path.exists`）
- 输入文件后缀校验（`.xlsx`）
- 输出目录可写性校验（`os.access`）
- 列存在性校验（读取表头后）

### 3.3 Excel Reader (`read_excel`)

- `pandas.read_excel(input_path, sheet_name=0)`
- 只读取第一个 sheet
- 指定 `dtype=str` 避免日期/数值自动转换问题

### 3.4 Aggregator (`aggregate`)

- `df.groupby(column).sum(numeric_only=True)`
- 自动检测数值列，忽略文本列
- 结果 reset_index() 使分组列恢复为普通列

### 3.5 CSV Writer (`write_csv`)

- `df.to_csv(output_path, index=False, encoding='utf-8-sig')`
- 使用 `utf-8-sig` 兼容 Excel 直接打开 CSV

## 4. Dependency Tree

```
aggregate.py
  ├── argparse (stdlib)
  ├── os.path (stdlib)
  ├── sys (stdlib)
  └── pandas (external)
       └── openpyxl (pandas engine for .xlsx)
```

总计外部依赖：2 个（pandas, openpyxl）
