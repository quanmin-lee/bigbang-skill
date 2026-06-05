"""CLI entry point for Excel summary tool."""

import argparse
import csv
import sys

from core import read_excel, summarize_column


def create_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser."""
    parser = argparse.ArgumentParser(description="Summarize numeric data from an Excel column.")
    parser.add_argument("--input", required=True, help="Path to input .xlsx file")
    parser.add_argument("--column", required=True, help="Column name to summarize")
    parser.add_argument("--output", default="output.csv", help="Output CSV path (default: output.csv)")
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    try:
        values = read_excel(args.input, args.column)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    summary = summarize_column(values)

    with open(args.output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["stat", "value"])
        for key in ["sum", "avg", "max", "min", "count"]:
            writer.writerow([key, summary[key]])

    print(f"Summary written to {args.output}")


if __name__ == "__main__":
    main()
