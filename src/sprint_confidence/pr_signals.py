"""US-5, US-6, US-9: merge-conflict, quality gate, and PR-split suggestion.

- US-5: a mergeable_state of "dirty" or "blocked" is a hard risk factor.
- US-6: a failing quality gate forces Red regardless of other signals;
  missing SonarQube data is flagged "unknown", never assumed to pass
  (Section 9).
- US-9: a text-only suggestion (never an automated action) when a Large
  PR that's already been assessed at risk is close to sprint end. "At
  risk" is decided by card_status.py (US-7), which combines PR and linked
  risk signals — this module only decides whether/when to surface the
  suggestion text once told a PR qualifies.
"""

from datetime import date
from typing import Optional

from .config import Thresholds
from .models import PullRequest

DIRTY_OR_BLOCKED_STATES = {"dirty", "blocked"}

QUALITY_GATE_PASS = "pass"
QUALITY_GATE_FAIL = "fail"
QUALITY_GATE_UNKNOWN = "unknown"


def merge_conflict_flag(pr: PullRequest) -> bool:
    return pr.mergeable is False or pr.mergeable_state in DIRTY_OR_BLOCKED_STATES


def quality_gate_flag(pr: PullRequest) -> str:
    if pr.sonarqube_quality_gate is None or pr.sonarqube_coverage_pct is None:
        return QUALITY_GATE_UNKNOWN
    return pr.sonarqube_quality_gate


def is_quality_gate_failing(pr: PullRequest) -> bool:
    return quality_gate_flag(pr) == QUALITY_GATE_FAIL


def pr_split_suggestion(
    pr: PullRequest,
    size_bucket: str,
    at_risk: bool,
    sprint_end_date: date,
    as_of_date: date,
    thresholds: Thresholds,
) -> Optional[str]:
    if size_bucket != "Large" or not at_risk:
        return None

    days_to_sprint_end = (sprint_end_date - as_of_date).days
    if days_to_sprint_end > thresholds.pr_split_suggestion_days_to_sprint_end:
        return None

    return (
        f"{pr.pr_id} is Large and at risk with {days_to_sprint_end} day(s) left in "
        "the sprint — consider splitting it into smaller, independently "
        "reviewable PRs."
    )
