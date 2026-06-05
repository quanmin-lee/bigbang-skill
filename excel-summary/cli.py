"""CLI entry point for Excel summary tool."""

import argparse
import csv
import sys

from core import read_excel, summarize_column


def main():
    parser = argparse.ArgumentParser(description="Summarize numeric data from an Excel column.")
    parser.add_argument("--input", required=True, help="Path to input .xlsx file")
    parser.add_argument("--column", required=True, help="Column name to summarize")
    parser.add_argument("--output", default="output.csv", help="Output CSV path (default: output.csv)")
    args = parser.parse_args()

    values = read_excel(args.input, args.column)
    summary = summarize_column(values)

    with open(args.output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["stat", "value"])
        for key in ["sum", "avg", "max", "min", "count"]:
            writer.writerow([key, summary[key]])

    print(f"Summary written to {args.output}")


if __name__ == "__main__":
    main()
