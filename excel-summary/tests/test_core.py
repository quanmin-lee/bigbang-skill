"""Tests for core module - read_excel function."""

import pytest
from core import read_excel


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
    with pytest.raises(ValueError, match="Column 'nonexistent' not found"):
        read_excel("sample.xlsx", "nonexistent")


def test_file_not_found():
    """Should raise FileNotFoundError for non-existent file."""
    with pytest.raises(FileNotFoundError, match="File not found"):
        read_excel("/nonexistent/path.xlsx", "score")
