"""Configurable thresholds referenced across user stories.

Defaults documented here per US-1's acceptance criterion ("defaults
documented if none supplied"). Values are placeholders pending US
implementation.
"""

from dataclasses import dataclass


@dataclass
class Thresholds:
    # US-1 and US-4: size bucket cutoffs, shared by initial PR diff and
    # round-2 rework diff. <= small_max is Small, <= medium_max is Medium,
    # above that is Large. Bucket is the worse of the lines-based and
    # files-based result.
    size_small_max_lines: int = 200
    size_medium_max_lines: int = 800
    size_small_max_files: int = 5
    size_medium_max_files: int = 15

    # US-3: days a review can sit "Pending" before being flagged
    pending_review_days: int = 3

    # US-6: SonarQube coverage threshold quoted in reasoning text alongside
    # the actual coverage_pct (does not itself decide pass/fail — the
    # mocked sonarqube_quality_gate field already says pass/fail directly)
    quality_gate_coverage_target_pct: int = 90

    # US-9: only suggest splitting a Large, at-risk PR once this few days
    # remain before the sprint ends
    pr_split_suggestion_days_to_sprint_end: int = 3

    # US-7/US-11: risk priority bucket cutoffs, from probability x impact
    # (1-5 scale each, so score ranges 1-25). <= low_max is Low,
    # <= medium_max is Medium, above that is High.
    risk_low_max_score: int = 6
    risk_medium_max_score: int = 14


DEFAULT_THRESHOLDS = Thresholds()
