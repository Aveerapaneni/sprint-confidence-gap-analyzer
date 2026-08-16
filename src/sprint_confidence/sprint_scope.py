"""US-10: Scope cards to each team's currently Active sprint.

For each team, resolve team.active_sprint_id against the sprints list,
confirm status == "active", and filter cards to that sprint_id. A team
with no Active sprint in the mock data is excluded and flagged explicitly
(Section 9 edge case), not silently dropped.
"""

from dataclasses import dataclass, field
from typing import Optional

from .models import Card, Sprint, Team


@dataclass
class SprintScopeResult:
    scoped_cards: list[Card]
    active_sprint_id_by_team: dict[str, str]
    excluded_teams: list[str] = field(default_factory=list)


def resolve_active_sprint(team: Team, sprints: list[Sprint]) -> Optional[Sprint]:
    for sprint in sprints:
        if sprint.sprint_id == team.active_sprint_id and sprint.status == "active":
            return sprint
    return None


def scope_cards_to_active_sprints(
    teams: list[Team], sprints: list[Sprint], cards: list[Card]
) -> SprintScopeResult:
    active_sprint_id_by_team: dict[str, str] = {}
    excluded_teams: list[str] = []

    for team in teams:
        active_sprint = resolve_active_sprint(team, sprints)
        if active_sprint is None:
            excluded_teams.append(team.team_id)
        else:
            active_sprint_id_by_team[team.team_id] = active_sprint.sprint_id

    active_sprint_ids = set(active_sprint_id_by_team.values())
    scoped_cards = [card for card in cards if card.sprint_id in active_sprint_ids]

    return SprintScopeResult(
        scoped_cards=scoped_cards,
        active_sprint_id_by_team=active_sprint_id_by_team,
        excluded_teams=excluded_teams,
    )
