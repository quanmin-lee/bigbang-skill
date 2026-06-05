"""Tests for CLI module."""

import os
import csv
import pytest
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_cli_output_file():
    """Should write correct CSV output with --output specified."""
    result = subprocess.run(
        [sys.executable, "cli.py", "--input", "sample.xlsx", "--column", "score", "--output", "test_output.csv"],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    assert result.returncode == 0
    output_path = os.path.join(PROJECT_ROOT, "test_output.csv")
    assert os.path.exists(output_path)
    with open(output_path, newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    os.remove(output_path)
    assert rows[0] == ["stat", "value"]
    assert len(rows) == 6  # header + 5 stats


def test_cli_default_output():
    """Should use default output.csv when --output not specified."""
    result = subprocess.run(
        [sys.executable, "cli.py", "--input", "sample.xlsx", "--column", "score"],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    assert result.returncode == 0
    output_path = os.path.join(PROJECT_ROOT, "output.csv")
    assert os.path.exists(output_path)
    os.remove(output_path)


def test_cli_file_not_found():
    """Should handle non-existent file gracefully."""
    result = subprocess.run(
        [sys.executable, "cli.py", "--input", "nonexistent.xlsx", "--column", "score"],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    assert result.returncode != 0
    assert "Error:" in result.stderr or "Error:" in result.stdout


def test_cli_missing_args():
    """Should show usage when required args missing."""
    result = subprocess.run(
        [sys.executable, "cli.py"],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    assert result.returncode != 0
    assert "usage:" in result.stderr.lower() or "usage:" in result.stdout.lower()


def test_cli_column_not_found():
    """Should handle non-existent column gracefully."""
    result = subprocess.run(
        [sys.executable, "cli.py", "--input", "sample.xlsx", "--column", "nonexistent"],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    assert result.returncode != 0
    assert "Error:" in result.stderr or "Error:" in result.stdout
