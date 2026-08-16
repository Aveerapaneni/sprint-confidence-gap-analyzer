"""Entry point: load data, load config/thresholds, run the pipeline, print
the report. Manually triggered by the PM, runs from the terminal (Section
6) — no scheduled/background execution, no network calls.

All thresholds are supplied at runtime via flags, each defaulting to the
documented values in config.DEFAULT_THRESHOLDS when omitted (US-1).
"""

import argparse
from datetime import date
from pathlib import Path
from typing import Optional

from src.sprint_confidence.config import DEFAULT_THRESHOLDS, Thresholds
from src.sprint_confidence.loader import (
    DEFAULT_DATA_DIR,
    load_features,
    load_prs,
    load_risks,
    load_sprints_and_cards,
    load_teams,
)
from src.sprint_confidence.report import build_report, render_report


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sprint Confidence Gap Analyzer — PR-derived confidence signals "
            "rolled up into per-card, feature, team, and Program-level status."
        )
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Directory with teams/features/cards/risks/prs.json (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--as-of",
        type=str,
        default=None,
        help="Date to evaluate the report as of, YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--pending-review-days",
        type=int,
        default=DEFAULT_THRESHOLDS.pending_review_days,
        help="Days a review can sit Pending before being flagged "
        f"(default: {DEFAULT_THRESHOLDS.pending_review_days})",
    )
    parser.add_argument(
        "--size-small-max-lines",
        type=int,
        default=DEFAULT_THRESHOLDS.size_small_max_lines,
        help=f"Max lines changed for a Small PR (default: {DEFAULT_THRESHOLDS.size_small_max_lines})",
    )
    parser.add_argument(
        "--size-medium-max-lines",
        type=int,
        default=DEFAULT_THRESHOLDS.size_medium_max_lines,
        help=f"Max lines changed for a Medium PR (default: {DEFAULT_THRESHOLDS.size_medium_max_lines})",
    )
    parser.add_argument(
        "--size-small-max-files",
        type=int,
        default=DEFAULT_THRESHOLDS.size_small_max_files,
        help=f"Max files changed for a Small PR (default: {DEFAULT_THRESHOLDS.size_small_max_files})",
    )
    parser.add_argument(
        "--size-medium-max-files",
        type=int,
        default=DEFAULT_THRESHOLDS.size_medium_max_files,
        help=f"Max files changed for a Medium PR (default: {DEFAULT_THRESHOLDS.size_medium_max_files})",
    )
    parser.add_argument(
        "--risk-low-max-score",
        type=int,
        default=DEFAULT_THRESHOLDS.risk_low_max_score,
        help="Max probability x impact score for a Low risk "
        f"(default: {DEFAULT_THRESHOLDS.risk_low_max_score})",
    )
    parser.add_argument(
        "--risk-medium-max-score",
        type=int,
        default=DEFAULT_THRESHOLDS.risk_medium_max_score,
        help="Max probability x impact score for a Medium risk "
        f"(default: {DEFAULT_THRESHOLDS.risk_medium_max_score})",
    )
    parser.add_argument(
        "--quality-gate-coverage-target-pct",
        type=int,
        default=DEFAULT_THRESHOLDS.quality_gate_coverage_target_pct,
        help="Coverage target percent quoted in reasoning text "
        f"(default: {DEFAULT_THRESHOLDS.quality_gate_coverage_target_pct})",
    )
    parser.add_argument(
        "--pr-split-suggestion-days-to-sprint-end",
        type=int,
        default=DEFAULT_THRESHOLDS.pr_split_suggestion_days_to_sprint_end,
        help="Days left in sprint at/below which a Large at-risk PR gets a split "
        f"suggestion (default: {DEFAULT_THRESHOLDS.pr_split_suggestion_days_to_sprint_end})",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    args = _parse_args(argv)

    thresholds = Thresholds(
        size_small_max_lines=args.size_small_max_lines,
        size_medium_max_lines=args.size_medium_max_lines,
        size_small_max_files=args.size_small_max_files,
        size_medium_max_files=args.size_medium_max_files,
        pending_review_days=args.pending_review_days,
        quality_gate_coverage_target_pct=args.quality_gate_coverage_target_pct,
        pr_split_suggestion_days_to_sprint_end=args.pr_split_suggestion_days_to_sprint_end,
        risk_low_max_score=args.risk_low_max_score,
        risk_medium_max_score=args.risk_medium_max_score,
    )
    as_of_date = date.fromisoformat(args.as_of) if args.as_of else date.today()

    teams = load_teams(args.data_dir)
    features = load_features(args.data_dir)
    sprints, cards = load_sprints_and_cards(args.data_dir)
    prs = load_prs(args.data_dir)
    risks = load_risks(args.data_dir)

    report = build_report(teams, features, sprints, cards, prs, risks, thresholds, as_of_date)
    print(render_report(report))


if __name__ == "__main__":
    main()
