"""US-8, US-14, US-15: shared "worst-status-wins" rollup logic.

worst_status() is the one primitive shared by all three scopes:
  - US-8:  team rollup — status counts + named at-risk cards with reasons.
  - US-14: program rollup — a team's own status is worst_status() of its
    cards, so "Red if any team has 1+ Red cards" falls out directly;
    Amber if any team is Amber with no Red; Green only if all teams
    clean. Teams with no Active sprint are excluded but explicitly named
    in the reasons (Section 9), not silently dropped.
  - US-15: feature rollup — worst_status() of its linked cards' statuses.
    A single-card feature simply inherits that card's status and
    reasoning directly, per the PRD's FEAT-02 example.

Reasoning for an at-risk rollup names which team(s)/card(s) are driving it.
"""

from dataclasses import dataclass

from .card_status import AMBER, GREEN, RED, CardStatusResult
from .models import Card, Feature, Team

_ORDER = {GREEN: 0, AMBER: 1, RED: 2}


def worst_status(statuses: list[str]) -> str:
    if not statuses:
        return GREEN
    return max(statuses, key=lambda status: _ORDER[status])


@dataclass
class AtRiskCard:
    card_id: str
    title: str
    status: str
    reasons: list[str]


@dataclass
class TeamRollup:
    team_id: str
    team_name: str
    status: str
    status_counts: dict[str, int]
    at_risk_cards: list[AtRiskCard]


@dataclass
class ProgramRollup:
    status: str
    reasons: list[str]
    team_rollups: list[TeamRollup]
    excluded_teams: list[str]


@dataclass
class FeatureRollup:
    feature_id: str
    feature_name: str
    status: str
    reasons: list[str]


def build_team_rollup(
    team: Team, card_results: list[CardStatusResult], cards_by_id: dict[str, Card]
) -> TeamRollup:
    counts = {RED: 0, AMBER: 0, GREEN: 0}
    at_risk_cards = []
    for result in card_results:
        counts[result.status] += 1
        if result.status != GREEN:
            card = cards_by_id[result.card_id]
            at_risk_cards.append(
                AtRiskCard(
                    card_id=result.card_id,
                    title=card.title,
                    status=result.status,
                    reasons=result.reasons,
                )
            )
    return TeamRollup(
        team_id=team.team_id,
        team_name=team.team_name,
        status=worst_status([r.status for r in card_results]),
        status_counts=counts,
        at_risk_cards=at_risk_cards,
    )


def build_program_rollup(
    team_rollups: list[TeamRollup], excluded_teams: list[str]
) -> ProgramRollup:
    status = worst_status([tr.status for tr in team_rollups])

    reasons = []
    if status != GREEN:
        for team_rollup in team_rollups:
            if team_rollup.status != status:
                continue
            card_ids = [c.card_id for c in team_rollup.at_risk_cards if c.status == status]
            reasons.append(f"{team_rollup.team_name} is {status}: {', '.join(card_ids)}")

    for team_id in excluded_teams:
        reasons.append(f"{team_id} excluded from Program rollup — no Active sprint found")

    return ProgramRollup(
        status=status, reasons=reasons, team_rollups=team_rollups, excluded_teams=excluded_teams
    )


def build_feature_rollup(
    feature: Feature,
    card_results_by_id: dict[str, CardStatusResult],
    cards_by_id: dict[str, Card],
) -> FeatureRollup:
    relevant = [
        card_results_by_id[card_id]
        for card_id in feature.linked_card_ids
        if card_id in card_results_by_id
    ]
    status = worst_status([r.status for r in relevant])

    if len(relevant) == 1:
        reasons = relevant[0].reasons
    else:
        reasons = []
        if status != GREEN:
            for result in relevant:
                if result.status != status:
                    continue
                card = cards_by_id[result.card_id]
                reasons.append(f"{card.card_id} ({card.title}) is {status}")

    return FeatureRollup(
        feature_id=feature.feature_id,
        feature_name=feature.feature_name,
        status=status,
        reasons=reasons,
    )
