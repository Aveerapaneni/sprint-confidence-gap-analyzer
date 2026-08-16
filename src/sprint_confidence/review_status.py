"""US-2, US-3, US-12: reviewer status, approvals-vs-required, pending duration.

Reviewers are expected to be drawn from the linked card's team's engineer
roster (US-12). Handles edge cases from Section 9: no reviewers assigned
("review not requested", not an error), a PR Approved and then updated
again ("needs re-review"), and mixed statuses (Changes Requested takes
precedence — the PR is treated as blocked regardless of approval count).
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from .config import Thresholds
from .dates import parse_date
from .models import PullRequest

APPROVED = "Approved"
CHANGES_REQUESTED = "Changes Requested"
PENDING = "Pending"


@dataclass
class ApprovalStatus:
    approvals_count: int
    required_approvals: int
    approvals_met: bool
    changes_requested: bool
    review_not_requested: bool


@dataclass
class PendingReviewer:
    reviewer_name: str
    days_pending: int


@dataclass
class StaleApprovalFlag:
    latest_approval_date: str
    last_updated_date: str


def approval_status(pr: PullRequest) -> ApprovalStatus:
    changes_requested = any(r.review_status == CHANGES_REQUESTED for r in pr.reviewers)
    approvals_count = sum(1 for r in pr.reviewers if r.review_status == APPROVED)
    return ApprovalStatus(
        approvals_count=approvals_count,
        required_approvals=pr.required_approvals,
        approvals_met=approvals_count >= pr.required_approvals and not changes_requested,
        changes_requested=changes_requested,
        review_not_requested=len(pr.reviewers) == 0,
    )


def pending_reviewers(
    pr: PullRequest, thresholds: Thresholds, as_of_date: date
) -> list[PendingReviewer]:
    flagged = []
    for reviewer in pr.reviewers:
        if reviewer.review_status != PENDING:
            continue
        days_pending = (as_of_date - parse_date(reviewer.last_action_date)).days
        if days_pending > thresholds.pending_review_days:
            flagged.append(PendingReviewer(reviewer.reviewer_name, days_pending))
    return flagged


def stale_approval(pr: PullRequest) -> Optional[StaleApprovalFlag]:
    """A PR is stale-approved when it was updated again after every current
    approval was given — i.e. the newest approval still predates
    last_updated_date, so those approvals no longer cover the latest diff.
    Returns None when there are no approvals yet, or when the PR hasn't
    been touched since its most recent approval."""
    approval_dates = [
        parse_date(r.last_action_date) for r in pr.reviewers if r.review_status == APPROVED
    ]
    if not approval_dates:
        return None

    latest_approval_date = max(approval_dates)
    last_updated = parse_date(pr.last_updated_date)
    if latest_approval_date < last_updated:
        return StaleApprovalFlag(
            latest_approval_date=latest_approval_date.isoformat(),
            last_updated_date=pr.last_updated_date,
        )
    return None


def invalid_reviewers(pr: PullRequest, team_engineers: list[str]) -> list[str]:
    """US-12: names any reviewer not drawn from the linked card's team's
    engineer roster. Expected to be empty for well-formed data."""
    return [r.reviewer_name for r in pr.reviewers if r.reviewer_name not in team_engineers]
