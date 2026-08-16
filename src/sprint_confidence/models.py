"""Typed data structures for teams, sprints, cards, features, PRs, and risks.

Mirrors the schema in Section 5 of the PRD. Populated by loader.py.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Team:
    team_id: str
    team_name: str
    velocity: int
    product_owner: str
    engineers: list[str]
    active_sprint_id: str


@dataclass
class Sprint:
    sprint_id: str
    team_id: str
    status: str
    start_date: str
    end_date: str
    sprint_goal: str


@dataclass
class Card:
    card_id: str
    team_id: str
    sprint_id: str
    title: str
    priority: str
    story_points: int
    status: str
    feature_id: str
    linked_pr_id: Optional[str]
    linked_risk_ids: list[str] = field(default_factory=list)


@dataclass
class Feature:
    feature_id: str
    feature_name: str
    description: str
    owner: str
    linked_team_ids: list[str]
    linked_card_ids: list[str]


@dataclass
class Reviewer:
    reviewer_name: str
    review_status: str
    last_action_date: str


@dataclass
class PullRequest:
    pr_id: str
    linked_card_id: str
    state: str
    created_date: str
    last_updated_date: str
    merged_date: Optional[str]
    lines_added: int
    lines_deleted: int
    files_changed: int
    reviewers: list[Reviewer]
    required_approvals: int
    round2_lines: Optional[int]
    round2_files: Optional[int]
    mergeable: bool
    mergeable_state: str
    ci_checks_status: str
    sonarqube_coverage_pct: Optional[int]
    sonarqube_quality_gate: Optional[str]


@dataclass
class Risk:
    risk_id: str
    category: str
    description: str
    owner: str
    probability: Optional[int]
    impact: int
    status: str
    linked_card_id: str
