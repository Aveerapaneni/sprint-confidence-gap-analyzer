"""Tests for pr_signals — US-5 (merge conflict), US-6 (quality gate),
US-9 (PR-split suggestion), and the Section 9 "quality gate unknown" edge
case."""

from datetime import date

from src.sprint_confidence.config import DEFAULT_THRESHOLDS, Thresholds
from src.sprint_confidence.loader import load_prs
from src.sprint_confidence.models import PullRequest
from src.sprint_confidence.pr_signals import (
    is_quality_gate_failing,
    merge_conflict_flag,
    pr_split_suggestion,
    quality_gate_flag,
)
from src.sprint_confidence.sizing import size_bucket


def _pr(**overrides) -> PullRequest:
    defaults = dict(
        pr_id="PR-TEST",
        linked_card_id="CARD-TEST",
        state="Open",
        created_date="2026-08-01",
        last_updated_date="2026-08-01",
        merged_date=None,
        lines_added=10,
        lines_deleted=0,
        files_changed=1,
        reviewers=[],
        required_approvals=1,
        round2_lines=None,
        round2_files=None,
        mergeable=True,
        mergeable_state="clean",
        ci_checks_status="pass",
        sonarqube_coverage_pct=90,
        sonarqube_quality_gate="pass",
    )
    defaults.update(overrides)
    return PullRequest(**defaults)


def test_merge_conflict_flag_clean_is_false():
    assert merge_conflict_flag(_pr(mergeable=True, mergeable_state="clean")) is False


def test_merge_conflict_flag_dirty_is_true():
    assert merge_conflict_flag(_pr(mergeable=False, mergeable_state="dirty")) is True


def test_merge_conflict_flag_blocked_is_true():
    assert merge_conflict_flag(_pr(mergeable=False, mergeable_state="blocked")) is True


def test_quality_gate_flag_pass_and_fail():
    assert quality_gate_flag(_pr(sonarqube_quality_gate="pass")) == "pass"
    assert quality_gate_flag(_pr(sonarqube_quality_gate="fail")) == "fail"
    assert is_quality_gate_failing(_pr(sonarqube_quality_gate="fail")) is True
    assert is_quality_gate_failing(_pr(sonarqube_quality_gate="pass")) is False


def test_quality_gate_flag_unknown_when_missing_never_assumed_pass():
    pr = _pr(sonarqube_quality_gate=None, sonarqube_coverage_pct=None)
    assert quality_gate_flag(pr) == "unknown"
    assert is_quality_gate_failing(pr) is False


def test_quality_gate_flag_unknown_when_partially_missing():
    pr = _pr(sonarqube_quality_gate="pass", sonarqube_coverage_pct=None)
    assert quality_gate_flag(pr) == "unknown"


def test_pr_split_suggestion_none_when_not_large():
    suggestion = pr_split_suggestion(
        _pr(),
        size_bucket="Medium",
        at_risk=True,
        sprint_end_date=date(2026, 8, 18),
        as_of_date=date(2026, 8, 16),
        thresholds=DEFAULT_THRESHOLDS,
    )
    assert suggestion is None


def test_pr_split_suggestion_none_when_not_at_risk():
    suggestion = pr_split_suggestion(
        _pr(),
        size_bucket="Large",
        at_risk=False,
        sprint_end_date=date(2026, 8, 18),
        as_of_date=date(2026, 8, 16),
        thresholds=DEFAULT_THRESHOLDS,
    )
    assert suggestion is None


def test_pr_split_suggestion_none_when_sprint_end_far_away():
    suggestion = pr_split_suggestion(
        _pr(),
        size_bucket="Large",
        at_risk=True,
        sprint_end_date=date(2026, 8, 30),
        as_of_date=date(2026, 8, 16),
        thresholds=DEFAULT_THRESHOLDS,
    )
    assert suggestion is None


def test_pr_split_suggestion_generated_when_qualifying():
    pr = _pr(pr_id="PR-9001")
    suggestion = pr_split_suggestion(
        pr,
        size_bucket="Large",
        at_risk=True,
        sprint_end_date=date(2026, 8, 18),
        as_of_date=date(2026, 8, 16),
        thresholds=DEFAULT_THRESHOLDS,
    )
    assert suggestion is not None
    assert "PR-9001" in suggestion
    assert "2 day(s)" in suggestion
    assert "splitting" in suggestion


def test_against_real_pr_data():
    prs = {pr.pr_id: pr for pr in load_prs()}

    pr1001 = prs["PR-1001"]
    assert merge_conflict_flag(pr1001) is False
    assert is_quality_gate_failing(pr1001) is True

    pr1004 = prs["PR-1004"]
    assert merge_conflict_flag(pr1004) is True
    assert is_quality_gate_failing(pr1004) is False

    # Under default thresholds none of the mock PRs reach Large — confirm
    # PR-1001 (the biggest one) crosses into Large only with tighter
    # thresholds, and that a suggestion is then produced.
    tight = Thresholds(size_small_max_lines=100, size_medium_max_lines=300)
    bucket = size_bucket(pr1001.lines_added, pr1001.lines_deleted, pr1001.files_changed, tight)
    assert bucket == "Large"
    suggestion = pr_split_suggestion(
        pr1001,
        size_bucket=bucket,
        at_risk=True,
        sprint_end_date=date(2026, 8, 18),
        as_of_date=date(2026, 8, 16),
        thresholds=DEFAULT_THRESHOLDS,
    )
    assert suggestion is not None
    assert "PR-1001" in suggestion
