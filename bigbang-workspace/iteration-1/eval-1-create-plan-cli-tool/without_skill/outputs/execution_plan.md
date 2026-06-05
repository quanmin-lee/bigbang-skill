# Execution Plan: Excel Aggregate CLI Tool

## Phase 0: Environment Setup

| Step | Action | Detail |
|------|--------|--------|
| 0.1 | 创建项目目录 | `mkdir excel-aggregator && cd excel-aggregator` |
| 0.2 | 创建虚拟环境 | `python -m venv venv` |
| 0.3 | 编写 requirements.txt | pandas, openpyxl |
| 0.4 | 安装依赖 | `pip install -r requirements.txt` |

## Phase 1: Core Implementation (aggregate.py)

| Step | Action | Detail |
|------|--------|--------|
| 1.1 | 编写 `parse_args()` | argparse 定义 --input, --column, --output |
| 1.2 | 编写 `validate_args()` | 文件存在、后缀、列名校验 |
| 1.3 | 编写 `read_and_aggregate()` | pandas groupby + sum |
| 1.4 | 编写 `write_output()` | CSV 输出, utf-8-sig |
| 1.5 | 编写 `main()` 入口 | if __name__ == "__main__" |
| 1.6 | 添加异常处理 | try/except 包裹关键步骤，输出可读错误信息 |

### 代码结构（伪代码）

```python
import argparse, os, sys, pandas as pd

def parse_args():
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("--input", required=True)
    parser.add_argument("--column", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()

def validate_args(args, columns):
    # 文件存在? 列存在?

def read_and_aggregate(input_path, group_col):
    df = pd.read_excel(input_path, sheet_name=0)
    if group_col not in df.columns:
        sys.exit(f"Column '{group_col}' not found")
    result = df.groupby(group_col).sum(numeric_only=True).reset_index()
    return result

def write_output(df, output_path):
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

def main():
    args = parse_args()
    df = read_and_aggregate(args.input, args.column)
    write_output(df, args.output)
    print(f"Done: {args.output}")

if __name__ == "__main__":
    main()
```

## Phase 2: Testing

| Step | Action | Detail |
|------|--------|--------|
| 2.1 | 创建测试 Excel 文件 | 用 openpyxl 创建含数值和文本列的测试文件 |
| 2.2 | 测试正常流程 | 指定 --column 分组汇总，验证 CSV 输出 |
| 2.3 | 测试文件不存在 | 验证错误提示 |
| 2.4 | 测试列不存在 | 验证错误提示 |
| 2.5 | 测试单个数值列 | 边界情况 |

## Phase 3: Documentation

| Step | Action | Detail |
|------|--------|--------|
| 3.1 | README.md 使用说明 | 安装、用法、示例 |

## Deliverables

```
excel-aggregator/
  ├── aggregate.py          # 主程序
  ├── requirements.txt      # 依赖
  └── README.md             # 使用说明
```

## Effort Estimate

| Phase | Estimated Time |
|-------|---------------|
| Phase 0 (Setup) | 5 min |
| Phase 1 (Core) | 20 min |
| Phase 2 (Testing) | 15 min |
| Phase 3 (Docs) | 10 min |
| **Total** | **~50 min** |
