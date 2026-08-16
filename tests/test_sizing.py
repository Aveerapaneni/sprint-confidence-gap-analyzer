"""Tests for sizing — US-1 (PR size bucket) and US-4 (round-2 size bucket)."""

from src.sprint_confidence.config import DEFAULT_THRESHOLDS, Thresholds
from src.sprint_confidence.loader import load_prs
from src.sprint_confidence.sizing import round2_size_bucket, size_bucket


def test_size_bucket_small():
    assert size_bucket(40, 12, 2, DEFAULT_THRESHOLDS) == "Small"


def test_size_bucket_medium():
    assert size_bucket(480, 140, 14, DEFAULT_THRESHOLDS) == "Medium"


def test_size_bucket_large_by_lines():
    assert size_bucket(900, 200, 3, DEFAULT_THRESHOLDS) == "Large"


def test_size_bucket_large_by_files_even_when_lines_are_small():
    assert size_bucket(50, 10, 20, DEFAULT_THRESHOLDS) == "Large"


def test_size_bucket_respects_custom_thresholds():
    tight = Thresholds(size_small_max_lines=10, size_medium_max_lines=50)
    assert size_bucket(60, 0, 1, tight) == "Large"


def test_round2_size_bucket_none_when_no_round2_yet():
    assert round2_size_bucket(None, None, DEFAULT_THRESHOLDS) is None


def test_round2_size_bucket_small_when_zero_diff():
    assert round2_size_bucket(0, 0, DEFAULT_THRESHOLDS) == "Small"


def test_round2_size_bucket_matches_size_bucket_logic():
    assert round2_size_bucket(180, 5, DEFAULT_THRESHOLDS) == "Small"


def test_against_real_pr_data():
    prs = {pr.pr_id: pr for pr in load_prs()}

    pr1001 = prs["PR-1001"]
    assert size_bucket(
        pr1001.lines_added, pr1001.lines_deleted, pr1001.files_changed, DEFAULT_THRESHOLDS
    ) == "Medium"
    assert round2_size_bucket(pr1001.round2_lines, pr1001.round2_files, DEFAULT_THRESHOLDS) == "Small"

    pr1002 = prs["PR-1002"]
    assert size_bucket(
        pr1002.lines_added, pr1002.lines_deleted, pr1002.files_changed, DEFAULT_THRESHOLDS
    ) == "Small"
    assert round2_size_bucket(pr1002.round2_lines, pr1002.round2_files, DEFAULT_THRESHOLDS) is None
