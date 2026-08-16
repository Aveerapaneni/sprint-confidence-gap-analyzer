"""Tests for review_status — US-2 (approvals), US-3 (pending duration),
US-12 (reviewer roster), and the Section 9 edge cases."""

from datetime import date

from src.sprint_confidence.config import DEFAULT_THRESHOLDS
from src.sprint_confidence.loader import load_prs, load_teams
from src.sprint_confidence.models import PullRequest, Reviewer
from src.sprint_confidence.review_status import (
    approval_status,
    invalid_reviewers,
    pending_reviewers,
    stale_approval,
)


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


def test_approval_status_no_reviewers_is_review_not_requested():
    pr = _pr(reviewers=[])
    status = approval_status(pr)
    assert status.review_not_requested is True
    assert status.approvals_count == 0
    assert status.approvals_met is False


def test_approval_status_changes_requested_blocks_even_with_enough_approvals():
    pr = _pr(
        required_approvals=1,
        reviewers=[
            Reviewer("Eng A", "Approved", "2026-08-02"),
            Reviewer("Eng B", "Changes Requested", "2026-08-03"),
        ],
    )
    status = approval_status(pr)
    assert status.approvals_count == 1
    assert status.changes_requested is True
    assert status.approvals_met is False


def test_approval_status_met_when_no_changes_requested():
    pr = _pr(
        required_approvals=2,
        reviewers=[
            Reviewer("Eng A", "Approved", "2026-08-02"),
            Reviewer("Eng B", "Approved", "2026-08-03"),
        ],
    )
    assert approval_status(pr).approvals_met is True


def test_pending_reviewers_flags_past_threshold():
    pr = _pr(reviewers=[Reviewer("Eng A", "Pending", "2026-08-05")])
    flagged = pending_reviewers(pr, DEFAULT_THRESHOLDS, as_of_date=date(2026, 8, 16))
    assert len(flagged) == 1
    assert flagged[0].reviewer_name == "Eng A"
    assert flagged[0].days_pending == 11


def test_pending_reviewers_not_flagged_within_threshold():
    pr = _pr(reviewers=[Reviewer("Eng A", "Pending", "2026-08-15")])
    flagged = pending_reviewers(pr, DEFAULT_THRESHOLDS, as_of_date=date(2026, 8, 16))
    assert flagged == []


def test_stale_approval_none_when_no_approvals():
    pr = _pr(reviewers=[Reviewer("Eng A", "Pending", "2026-08-05")])
    assert stale_approval(pr) is None


def test_stale_approval_none_when_approval_matches_last_update():
    pr = _pr(
        last_updated_date="2026-08-06",
        reviewers=[
            Reviewer("Eng A", "Approved", "2026-08-05"),
            Reviewer("Eng B", "Approved", "2026-08-06"),
        ],
    )
    assert stale_approval(pr) is None


def test_stale_approval_flagged_when_updated_after_latest_approval():
    pr = _pr(
        last_updated_date="2026-08-09",
        reviewers=[Reviewer("Eng A", "Approved", "2026-08-07")],
    )
    flag = stale_approval(pr)
    assert flag is not None
    assert flag.latest_approval_date == "2026-08-07"
    assert flag.last_updated_date == "2026-08-09"


def test_invalid_reviewers_flags_names_outside_roster():
    pr = _pr(reviewers=[Reviewer("Not On Team", "Approved", "2026-08-02")])
    assert invalid_reviewers(pr, ["Eng A", "Eng B"]) == ["Not On Team"]


def test_invalid_reviewers_empty_when_all_valid():
    pr = _pr(reviewers=[Reviewer("Eng A", "Approved", "2026-08-02")])
    assert invalid_reviewers(pr, ["Eng A", "Eng B"]) == []


def test_against_real_pr_and_team_data():
    prs = {pr.pr_id: pr for pr in load_prs()}
    teams = {t.team_id: t for t in load_teams()}
    alpha_engineers = teams["team_alpha"].engineers

    pr1001 = prs["PR-1001"]
    status = approval_status(pr1001)
    assert status.approvals_count == 1
    assert status.changes_requested is True
    assert status.approvals_met is False
    assert invalid_reviewers(pr1001, alpha_engineers) == []
    stale = stale_approval(pr1001)
    assert stale is not None
    assert stale.latest_approval_date == "2026-08-07"

    pr1002 = prs["PR-1002"]
    assert approval_status(pr1002).review_not_requested is True

    pr1003 = prs["PR-1003"]
    assert approval_status(pr1003).approvals_met is True
    assert stale_approval(pr1003) is None

    pr1004 = prs["PR-1004"]
    flagged = pending_reviewers(pr1004, DEFAULT_THRESHOLDS, as_of_date=date(2026, 8, 16))
    assert len(flagged) == 1
    assert flagged[0].reviewer_name == "Taylor Singh"
