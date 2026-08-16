"""US-7 and US-13: combine PR + risk signals into one card-level RAG status
with plain-English reasoning.

Status logic (US-7 acceptance criterion):
  - Red: any hard-fail signal — a failing quality gate, a merge conflict,
    or an associated active High-priority Risk/Issue.
  - Amber: one or more soft-risk signals present, no hard-fail.
  - Green: clean across all signals — no flags of either kind.

Note on "multiple soft-risk signals = Amber" (US-7): read here as "one or
more". A single soft signal — e.g. "Changes Requested" or an unknown
quality gate — is still worth surfacing to a PM rather than reported
Green; the PRD's own Problem Statement goal is catching risk before
last-minute standup surprises, which a stricter "needs 2+ signals" bar
would work against.

Reasoning (US-13) is rule-based text generated from the already-computed
flags — no LLM call, zero additional cost (Section 4.2).
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from .config import Thresholds
from .models import Card, PullRequest, Risk
from .pr_signals import merge_conflict_flag, pr_split_suggestion, quality_gate_flag
from .review_status import approval_status, pending_reviewers, stale_approval
from .risk_linking import HIGH, linked_active_risks
from .sizing import round2_size_bucket, size_bucket

RED = "Red"
AMBER = "Amber"
GREEN = "Green"

DONE_STATUS = "done"


@dataclass
class Flag:
    category: str
    text: str


@dataclass
class CardStatusResult:
    card_id: str
    status: str
    hard_flags: list[Flag]
    soft_flags: list[Flag]
    pr_split_suggestion: Optional[str] = None

    @property
    def reasons(self) -> list[str]:
        return build_reasoning(self.hard_flags + self.soft_flags)


def build_reasoning(flags: list[Flag]) -> list[str]:
    return [flag.text for flag in flags]


def _no_pr_flags(card: Card) -> list[Flag]:
    """Section 9: no linked PR yet is flagged distinctly from 'PR exists
    but at risk' — and only matters while the card isn't already done."""
    if card.linked_pr_id is None and card.status != DONE_STATUS:
        return [Flag("no_pr", "No linked PR yet — work not started")]
    return []


def _pr_hard_flags(pr: PullRequest, thresholds: Thresholds) -> list[Flag]:
    flags = []
    if quality_gate_flag(pr) == "fail":
        flags.append(
            Flag(
                "quality_gate_fail",
                f"Quality gate failed: {pr.sonarqube_coverage_pct}% coverage, "
                f"threshold {thresholds.quality_gate_coverage_target_pct}%",
            )
        )
    if merge_conflict_flag(pr):
        flags.append(
            Flag("merge_conflict", f"Merge conflict: mergeable_state is '{pr.mergeable_state}'")
        )
    return flags


def _pr_soft_flags(pr: PullRequest, thresholds: Thresholds, as_of_date: date) -> list[Flag]:
    flags: list[Flag] = []

    approval = approval_status(pr)
    if approval.review_not_requested:
        flags.append(Flag("review_not_requested", "No reviewer assigned yet — review not requested"))
    elif approval.changes_requested:
        flags.append(
            Flag("changes_requested", "Changes requested by a reviewer — PR blocked pending rework")
        )
    elif not approval.approvals_met:
        flags.append(
            Flag(
                "insufficient_approvals",
                f"Only {approval.approvals_count} of {approval.required_approvals} "
                "required approvals received",
            )
        )

    for pending in pending_reviewers(pr, thresholds, as_of_date):
        flags.append(
            Flag(
                "pending_review",
                f"Review from {pending.reviewer_name} pending {pending.days_pending} day(s) "
                f"(threshold {thresholds.pending_review_days})",
            )
        )

    stale = stale_approval(pr)
    if stale is not None:
        flags.append(
            Flag(
                "stale_approval",
                f"PR updated on {stale.last_updated_date} after the most recent approval on "
                f"{stale.latest_approval_date} — needs re-review",
            )
        )

    if round2_size_bucket(pr.round2_lines, pr.round2_files, thresholds) == "Large":
        flags.append(
            Flag("round2_large", "Round 2 rework is Large — significant post-review changes")
        )

    if quality_gate_flag(pr) == "unknown":
        flags.append(
            Flag(
                "quality_gate_unknown",
                "Quality gate status unknown — SonarQube data missing, not assumed to pass",
            )
        )

    return flags


def _risk_flags(
    card: Card, risks_by_id: dict[str, Risk], thresholds: Thresholds
) -> tuple[list[Flag], list[Flag]]:
    hard: list[Flag] = []
    soft: list[Flag] = []
    for linked in linked_active_risks(card, risks_by_id, thresholds):
        risk = linked.risk
        text = f"Active {linked.priority}-priority {risk.category}: {risk.description} ({risk.risk_id})"
        if linked.priority == HIGH:
            hard.append(Flag("high_priority_risk", text))
        else:
            soft.append(Flag("active_risk", text))
    return hard, soft


def compute_card_status(
    card: Card,
    pr: Optional[PullRequest],
    risks_by_id: dict[str, Risk],
    thresholds: Thresholds,
    as_of_date: date,
    sprint_end_date: Optional[date] = None,
) -> CardStatusResult:
    hard_flags: list[Flag] = []
    soft_flags: list[Flag] = list(_no_pr_flags(card))

    if pr is not None:
        hard_flags += _pr_hard_flags(pr, thresholds)
        soft_flags += _pr_soft_flags(pr, thresholds, as_of_date)

    risk_hard, risk_soft = _risk_flags(card, risks_by_id, thresholds)
    hard_flags += risk_hard
    soft_flags += risk_soft

    if hard_flags:
        status = RED
    elif soft_flags:
        status = AMBER
    else:
        status = GREEN

    suggestion = None
    if pr is not None and sprint_end_date is not None:
        bucket = size_bucket(pr.lines_added, pr.lines_deleted, pr.files_changed, thresholds)
        suggestion = pr_split_suggestion(
            pr,
            size_bucket=bucket,
            at_risk=status in (RED, AMBER),
            sprint_end_date=sprint_end_date,
            as_of_date=as_of_date,
            thresholds=thresholds,
        )

    return CardStatusResult(
        card_id=card.card_id,
        status=status,
        hard_flags=hard_flags,
        soft_flags=soft_flags,
        pr_split_suggestion=suggestion,
    )
