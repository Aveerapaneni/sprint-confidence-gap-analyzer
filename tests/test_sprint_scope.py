"""Tests for sprint_scope — US-10 active-sprint scoping, including the
no-Active-sprint edge case from Section 9."""

from src.sprint_confidence.loader import load_sprints_and_cards, load_teams
from src.sprint_confidence.models import Card, Sprint, Team
from src.sprint_confidence.sprint_scope import (
    resolve_active_sprint,
    scope_cards_to_active_sprints,
)


def test_resolve_active_sprint_matches_and_confirms_status():
    team = Team(
        team_id="team_x",
        team_name="Team X",
        velocity=10,
        product_owner="PO",
        engineers=["Eng A"],
        active_sprint_id="sprint_x1",
    )
    sprints = [
        Sprint(
            sprint_id="sprint_x1",
            team_id="team_x",
            status="active",
            start_date="2026-01-01",
            end_date="2026-01-14",
            sprint_goal="Goal",
        )
    ]
    resolved = resolve_active_sprint(team, sprints)
    assert resolved is not None
    assert resolved.sprint_id == "sprint_x1"


def test_resolve_active_sprint_returns_none_when_not_active():
    team = Team(
        team_id="team_x",
        team_name="Team X",
        velocity=10,
        product_owner="PO",
        engineers=["Eng A"],
        active_sprint_id="sprint_x1",
    )
    sprints = [
        Sprint(
            sprint_id="sprint_x1",
            team_id="team_x",
            status="closed",
            start_date="2026-01-01",
            end_date="2026-01-14",
            sprint_goal="Goal",
        )
    ]
    assert resolve_active_sprint(team, sprints) is None


def test_resolve_active_sprint_returns_none_when_id_not_found():
    team = Team(
        team_id="team_x",
        team_name="Team X",
        velocity=10,
        product_owner="PO",
        engineers=["Eng A"],
        active_sprint_id="sprint_missing",
    )
    assert resolve_active_sprint(team, []) is None


def test_scope_cards_to_active_sprints_with_real_data():
    teams = load_teams()
    sprints, cards = load_sprints_and_cards()

    result = scope_cards_to_active_sprints(teams, sprints, cards)

    assert result.excluded_teams == []
    assert result.active_sprint_id_by_team == {
        "team_alpha": "sprint_12",
        "team_bravo": "sprint_09",
        "team_charlie": "sprint_15",
    }
    assert len(result.scoped_cards) == len(cards)


def test_scope_cards_excludes_team_with_no_active_sprint():
    teams = [
        Team(
            team_id="team_x",
            team_name="Team X",
            velocity=10,
            product_owner="PO",
            engineers=["Eng A"],
            active_sprint_id="sprint_x1",
        ),
        Team(
            team_id="team_y",
            team_name="Team Y",
            velocity=10,
            product_owner="PO",
            engineers=["Eng B"],
            active_sprint_id="sprint_y1",
        ),
    ]
    sprints = [
        Sprint(
            sprint_id="sprint_x1",
            team_id="team_x",
            status="active",
            start_date="2026-01-01",
            end_date="2026-01-14",
            sprint_goal="Goal",
        ),
        Sprint(
            sprint_id="sprint_y1",
            team_id="team_y",
            status="closed",
            start_date="2026-01-01",
            end_date="2026-01-14",
            sprint_goal="Goal",
        ),
    ]
    cards = [
        Card(
            card_id="X-1",
            team_id="team_x",
            sprint_id="sprint_x1",
            title="Card in active sprint",
            priority="high",
            story_points=3,
            status="in_progress",
            feature_id="FEAT-X",
            linked_pr_id=None,
        ),
        Card(
            card_id="Y-1",
            team_id="team_y",
            sprint_id="sprint_y1",
            title="Card in closed sprint",
            priority="high",
            story_points=3,
            status="in_progress",
            feature_id="FEAT-Y",
            linked_pr_id=None,
        ),
    ]

    result = scope_cards_to_active_sprints(teams, sprints, cards)

    assert result.active_sprint_id_by_team == {"team_x": "sprint_x1"}
    assert result.excluded_teams == ["team_y"]
    assert [c.card_id for c in result.scoped_cards] == ["X-1"]
