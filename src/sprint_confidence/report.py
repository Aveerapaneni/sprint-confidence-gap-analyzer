"""Assemble the final CLI-printable report: card-level, feature-level,
team-level, and Program-level status with reasoning (Definition of Done).

build_report() wires together every module built so far:
  1. sprint_scope — scope cards to each team's Active sprint (US-10).
  2. card_status  — compute Red/Amber/Green + reasoning per scoped card
     (US-7, US-13).
  3. rollup       — team (US-8), Program (US-14), and feature (US-15)
     rollups on top of those card results.

render_report() turns that into the non-technical-stakeholder-readable
text the CLI prints (Section 8 Usability NFR).
"""

from dataclasses import dataclass
from datetime import date

from .card_status import CardStatusResult, compute_card_status
from .config import Thresholds
from .dates import parse_date
from .models import Card, Feature, PullRequest, Risk, Sprint, Team
from .rollup import (
    FeatureRollup,
    ProgramRollup,
    TeamRollup,
    build_feature_rollup,
    build_program_rollup,
    build_team_rollup,
)
from .sprint_scope import scope_cards_to_active_sprints


@dataclass
class Report:
    as_of_date: date
    active_sprint_id_by_team: dict[str, str]
    excluded_teams: list[str]
    card_results: dict[str, CardStatusResult]
    team_rollups: list[TeamRollup]
    program_rollup: ProgramRollup
    feature_rollups: list[FeatureRollup]


def build_report(
    teams: list[Team],
    features: list[Feature],
    sprints: list[Sprint],
    cards: list[Card],
    prs: list[PullRequest],
    risks: list[Risk],
    thresholds: Thresholds,
    as_of_date: date,
) -> Report:
    scope = scope_cards_to_active_sprints(teams, sprints, cards)

    prs_by_id = {pr.pr_id: pr for pr in prs}
    risks_by_id = {risk.risk_id: risk for risk in risks}
    sprints_by_id = {sprint.sprint_id: sprint for sprint in sprints}
    cards_by_id = {card.card_id: card for card in scope.scoped_cards}

    card_results: dict[str, CardStatusResult] = {}
    for card in scope.scoped_cards:
        pr = prs_by_id.get(card.linked_pr_id) if card.linked_pr_id else None
        sprint = sprints_by_id.get(card.sprint_id)
        sprint_end_date = parse_date(sprint.end_date) if sprint else None
        card_results[card.card_id] = compute_card_status(
            card, pr, risks_by_id, thresholds, as_of_date, sprint_end_date
        )

    team_rollups = []
    for team in teams:
        if team.team_id not in scope.active_sprint_id_by_team:
            continue
        team_cards = [c for c in scope.scoped_cards if c.team_id == team.team_id]
        team_results = [card_results[c.card_id] for c in team_cards]
        team_rollups.append(build_team_rollup(team, team_results, cards_by_id))

    program_rollup = build_program_rollup(team_rollups, scope.excluded_teams)

    feature_rollups = [
        build_feature_rollup(feature, card_results, cards_by_id) for feature in features
    ]

    return Report(
        as_of_date=as_of_date,
        active_sprint_id_by_team=scope.active_sprint_id_by_team,
        excluded_teams=scope.excluded_teams,
        card_results=card_results,
        team_rollups=team_rollups,
        program_rollup=program_rollup,
        feature_rollups=feature_rollups,
    )


def render_report(report: Report) -> str:
    lines: list[str] = []

    lines.append("Sprint Confidence Gap Analyzer")
    lines.append(f"As of: {report.as_of_date.isoformat()}")
    lines.append("")

    lines.append("Active sprints:")
    for team_id, sprint_id in report.active_sprint_id_by_team.items():
        lines.append(f"  {team_id}: {sprint_id}")
    if report.excluded_teams:
        lines.append(f"  Excluded (no Active sprint): {', '.join(report.excluded_teams)}")
    lines.append("")

    lines.append(f"PROGRAM STATUS: {report.program_rollup.status}")
    for reason in report.program_rollup.reasons:
        lines.append(f"  - {reason}")
    lines.append("")

    lines.append("FEATURES")
    for feature_rollup in report.feature_rollups:
        lines.append(
            f"  {feature_rollup.feature_id} {feature_rollup.feature_name}: {feature_rollup.status}"
        )
        for reason in feature_rollup.reasons:
            lines.append(f"    - {reason}")
    lines.append("")

    lines.append("TEAMS")
    for team_rollup in report.team_rollups:
        counts = team_rollup.status_counts
        lines.append(
            f"  {team_rollup.team_name}: {team_rollup.status} "
            f"(Red: {counts['Red']}, Amber: {counts['Amber']}, Green: {counts['Green']})"
        )
        if team_rollup.at_risk_cards:
            lines.append("    At-risk cards:")
            for card in team_rollup.at_risk_cards:
                lines.append(f"      {card.card_id} [{card.status}] {card.title}")
                for reason in card.reasons:
                    lines.append(f"        - {reason}")

    return "\n".join(lines)
