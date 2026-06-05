"""Tests for core module."""

import os
import pytest
import openpyxl
from core import read_excel, summarize_column


@pytest.fixture
def empty_sheet_path(tmp_path):
    """Create an xlsx file with only a header row (no data)."""
    path = str(tmp_path / "empty.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["name", "score", "grade"])
    wb.save(path)
    return path


def test_read_numeric_column():
    """Should extract numeric values from a column."""
    result = read_excel("sample.xlsx", "score")
    assert result == [50, 60, 70, 80, 90, 100, 110, 120, 130, 140]


def test_read_amount_column_with_empty():
    """Should skip empty cells and extract only numeric values."""
    result = read_excel("sample.xlsx", "amount")
    assert result == [100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0]


def test_read_non_numeric_column():
    """Should return empty list for text-only column."""
    result = read_excel("sample.xlsx", "grade")
    assert result == []


def test_column_not_found():
    """Should raise ValueError for non-existent column."""
    with pytest.raises(ValueError, match="Column 'nonexistent' not found in spreadsheet"):
        read_excel("sample.xlsx", "nonexistent")


def test_file_not_found():
    """Should raise FileNotFoundError for non-existent file."""
    with pytest.raises(FileNotFoundError, match="File not found"):
        read_excel("/nonexistent/path.xlsx", "score")


def test_summarize_normal_case():
    """Should compute correct statistics for a list of numbers."""
    result = summarize_column([50, 60, 70, 80, 90])
    assert result["sum"] == 350
    assert result["avg"] == 70
    assert result["max"] == 90
    assert result["min"] == 50
    assert result["count"] == 5


def test_summarize_with_duplicates():
    """Should count unique values (deduplicated)."""
    result = summarize_column([100, 100, 200, 200])
    assert result["sum"] == 600
    assert result["avg"] == 150
    assert result["max"] == 200
    assert result["min"] == 100
    assert result["count"] == 2


def test_summarize_empty_list():
    """Should return zeros for empty list."""
    result = summarize_column([])
    assert result["sum"] == 0
    assert result["avg"] == 0
    assert result["max"] == 0
    assert result["min"] == 0
    assert result["count"] == 0


def test_summarize_single_element():
    """Should handle single-element list correctly."""
    result = summarize_column([42])
    assert result["sum"] == 42
    assert result["avg"] == 42
    assert result["max"] == 42
    assert result["min"] == 42
    assert result["count"] == 1


def test_summarize_negative_numbers():
    """Should handle negative numbers correctly."""
    result = summarize_column([-10, -5, 0, 5, 10])
    assert result["sum"] == 0
    assert result["avg"] == 0
    assert result["max"] == 10
    assert result["min"] == -10
    assert result["count"] == 5


def test_summarize_float_precision():
    """Should handle floating-point values correctly."""
    result = summarize_column([1.5, 2.5, 3.0])
    assert result["sum"] == 7.0
    assert result["avg"] == 7.0 / 3
    assert result["max"] == 3.0
    assert result["min"] == 1.5
    assert result["count"] == 3


def test_read_empty_sheet_returns_empty_list(empty_sheet_path):
    """Should return empty list when sheet has header but no data rows."""
    result = read_excel(empty_sheet_path, "score")
    assert result == []
    summary = summarize_column(result)
    assert summary["sum"] == 0
    assert summary["count"] == 0


def test_read_large_numbers():
    """Should handle very large numeric values."""
    result = read_excel("sample.xlsx", "score")
    large = 10_000_000_000
    result.append(large)
    summary = summarize_column(result)
    assert summary["max"] == large
