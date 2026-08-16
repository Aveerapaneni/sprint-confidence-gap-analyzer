"""Tests for rollup — US-8 (team), US-14 (program), US-15 (feature), and
the Section 9 "team with no Active sprint" edge case."""

from datetime import date

from src.sprint_confidence.card_status import AMBER, GREEN, RED, compute_card_status
from src.sprint_confidence.config import DEFAULT_THRESHOLDS
from src.sprint_confidence.loader import (
    load_features,
    load_prs,
    load_risks,
    load_sprints_and_cards,
    load_teams,
)
from src.sprint_confidence.rollup import (
    AtRiskCard,
    TeamRollup,
    build_feature_rollup,
    build_program_rollup,
    build_team_rollup,
    worst_status,
)

AS_OF = date(2026, 8, 16)


def test_worst_status_precedence():
    assert worst_status([]) == GREEN
    assert worst_status([GREEN, GREEN]) == GREEN
    assert worst_status([GREEN, AMBER]) == AMBER
    assert worst_status([GREEN, AMBER, RED]) == RED
    assert worst_status([RED, RED]) == RED


def _compute_all_card_results():
    risks_by_id = {r.risk_id: r for r in load_risks()}
    prs_by_id = {p.pr_id: p for p in load_prs()}
    _, cards = load_sprints_and_cards()

    results = {}
    for card in cards:
        pr = prs_by_id.get(card.linked_pr_id) if card.linked_pr_id else None
        results[card.card_id] = compute_card_status(card, pr, risks_by_id, DEFAULT_THRESHOLDS, AS_OF)
    return results, {c.card_id: c for c in cards}


def test_team_rollup_against_real_data():
    results, cards_by_id = _compute_all_card_results()
    teams_by_id = {t.team_id: t for t in load_teams()}

    alpha_cards = [c for c in cards_by_id.values() if c.team_id == "team_alpha"]
    alpha_results = [results[c.card_id] for c in alpha_cards]
    alpha_rollup = build_team_rollup(teams_by_id["team_alpha"], alpha_results, cards_by_id)

    assert alpha_rollup.status == RED
    assert alpha_rollup.status_counts == {RED: 1, AMBER: 1, GREEN: 2}
    assert {c.card_id for c in alpha_rollup.at_risk_cards} == {"ALPHA-202", "ALPHA-204"}

    bravo_cards = [c for c in cards_by_id.values() if c.team_id == "team_bravo"]
    bravo_results = [results[c.card_id] for c in bravo_cards]
    bravo_rollup = build_team_rollup(teams_by_id["team_bravo"], bravo_results, cards_by_id)
    assert bravo_rollup.status == RED
    assert bravo_rollup.status_counts == {RED: 1, AMBER: 1, GREEN: 2}

    charlie_cards = [c for c in cards_by_id.values() if c.team_id == "team_charlie"]
    charlie_results = [results[c.card_id] for c in charlie_cards]
    charlie_rollup = build_team_rollup(teams_by_id["team_charlie"], charlie_results, cards_by_id)
    assert charlie_rollup.status == RED
    assert charlie_rollup.status_counts == {RED: 1, AMBER: 0, GREEN: 1}


def test_program_rollup_against_real_data():
    results, cards_by_id = _compute_all_card_results()
    teams_by_id = {t.team_id: t for t in load_teams()}

    team_rollups = []
    for team_id in ("team_alpha", "team_bravo", "team_charlie"):
        team_cards = [c for c in cards_by_id.values() if c.team_id == team_id]
        team_results = [results[c.card_id] for c in team_cards]
        team_rollups.append(build_team_rollup(teams_by_id[team_id], team_results, cards_by_id))

    program = build_program_rollup(team_rollups, excluded_teams=[])

    assert program.status == RED
    assert program.excluded_teams == []
    assert any("ALPHA-202" in r for r in program.reasons)
    assert any("BRAVO-102" in r for r in program.reasons)
    assert any("CHAR-301" in r for r in program.reasons)


def test_program_rollup_flags_excluded_team_explicitly():
    green_rollup = TeamRollup(
        team_id="team_x",
        team_name="Team X",
        status=GREEN,
        status_counts={RED: 0, AMBER: 0, GREEN: 3},
        at_risk_cards=[],
    )
    program = build_program_rollup([green_rollup], excluded_teams=["team_y"])

    assert program.status == GREEN
    assert program.reasons == ["team_y excluded from Program rollup — no Active sprint found"]


def test_program_rollup_green_when_all_teams_clean():
    green_rollup = TeamRollup(
        team_id="team_x",
        team_name="Team X",
        status=GREEN,
        status_counts={RED: 0, AMBER: 0, GREEN: 3},
        at_risk_cards=[],
    )
    program = build_program_rollup([green_rollup], excluded_teams=[])
    assert program.status == GREEN
    assert program.reasons == []


def test_program_rollup_amber_when_no_team_is_red():
    amber_rollup = TeamRollup(
        team_id="team_x",
        team_name="Team X",
        status=AMBER,
        status_counts={RED: 0, AMBER: 1, GREEN: 2},
        at_risk_cards=[AtRiskCard("X-1", "Card X-1", AMBER, ["some soft signal"])],
    )
    program = build_program_rollup([amber_rollup], excluded_teams=[])
    assert program.status == AMBER
    assert any("X-1" in r for r in program.reasons)


def test_feature_rollup_single_card_inherits_status_and_reasoning():
    results, cards_by_id = _compute_all_card_results()
    features = {f.feature_id: f for f in load_features()}

    feat02 = build_feature_rollup(features["FEAT-02"], results, cards_by_id)

    assert feat02.status == results["ALPHA-202"].status == RED
    assert feat02.reasons == results["ALPHA-202"].reasons
    assert feat02.reasons != []


def test_feature_rollup_multi_card_worst_wins_and_names_driver():
    results, cards_by_id = _compute_all_card_results()
    features = {f.feature_id: f for f in load_features()}

    feat01 = build_feature_rollup(features["FEAT-01"], results, cards_by_id)
    assert feat01.status == AMBER
    assert any("ALPHA-204" in r for r in feat01.reasons)

    feat03 = build_feature_rollup(features["FEAT-03"], results, cards_by_id)
    assert feat03.status == RED
    assert any("BRAVO-102" in r for r in feat03.reasons)

    feat04 = build_feature_rollup(features["FEAT-04"], results, cards_by_id)
    assert feat04.status == RED
    assert any("CHAR-301" in r for r in feat04.reasons)
