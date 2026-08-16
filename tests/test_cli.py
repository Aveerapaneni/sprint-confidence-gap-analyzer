"""Tests for cli — argument parsing and the end-to-end run against the
real mock data (US-1's "thresholds supplied at runtime" requirement)."""

import subprocess
import sys
from pathlib import Path

from cli import _parse_args, main

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_parse_args_defaults_match_documented_thresholds():
    from src.sprint_confidence.config import DEFAULT_THRESHOLDS

    args = _parse_args([])
    assert args.pending_review_days == DEFAULT_THRESHOLDS.pending_review_days
    assert args.size_small_max_lines == DEFAULT_THRESHOLDS.size_small_max_lines
    assert args.size_medium_max_lines == DEFAULT_THRESHOLDS.size_medium_max_lines
    assert args.risk_low_max_score == DEFAULT_THRESHOLDS.risk_low_max_score
    assert args.as_of is None


def test_parse_args_overrides():
    args = _parse_args(["--pending-review-days", "10", "--as-of", "2026-08-16"])
    assert args.pending_review_days == 10
    assert args.as_of == "2026-08-16"


def test_main_runs_end_to_end_against_real_data(capsys):
    main(["--as-of", "2026-08-16"])
    out = capsys.readouterr().out

    assert "PROGRAM STATUS: Red" in out
    assert "ALPHA-202" in out
    assert "FEAT-02 Payment Reliability: Red" in out


def test_main_threshold_override_changes_output(capsys):
    main(["--as-of", "2026-08-16", "--pending-review-days", "30"])
    out = capsys.readouterr().out
    assert "Taylor Singh" not in out


def test_cli_runs_as_a_subprocess():
    result = subprocess.run(
        [sys.executable, "cli.py", "--as-of", "2026-08-16"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "PROGRAM STATUS: Red" in result.stdout
