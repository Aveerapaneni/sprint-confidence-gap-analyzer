"""Tests for report — the end-to-end pipeline (US-10 scoping through
US-7/8/14/15 status and rollups) and the plain-text render (Section 8
Usability NFR)."""

from datetime import date

from src.sprint_confidence.config import DEFAULT_THRESHOLDS
from src.sprint_confidence.loader import (
    load_features,
    load_prs,
    load_risks,
    load_sprints_and_cards,
    load_teams,
)
from src.sprint_confidence.report import build_report, render_report
from src.sprint_confidence.sprint_scope import SprintScopeResult

AS_OF = date(2026, 8, 16)


def _build_real_report():
    teams = load_teams()
    features = load_features()
    sprints, cards = load_sprints_and_cards()
    prs = load_prs()
    risks = load_risks()
    return build_report(teams, features, sprints, cards, prs, risks, DEFAULT_THRESHOLDS, AS_OF)


def test_build_report_scoping_matches_teams_active_sprints():
    report = _build_real_report()
    assert report.active_sprint_id_by_team == {
        "team_alpha": "sprint_12",
        "team_bravo": "sprint_09",
        "team_charlie": "sprint_15",
    }
    assert report.excluded_teams == []
    assert len(report.card_results) == 10


def test_build_report_card_statuses_match_expected():
    report = _build_real_report()
    expected = {
        "ALPHA-201": "Green",
        "ALPHA-202": "Red",
        "ALPHA-203": "Green",
        "ALPHA-204": "Amber",
        "BRAVO-101": "Green",
        "BRAVO-102": "Red",
        "BRAVO-103": "Green",
        "BRAVO-104": "Amber",
        "CHAR-301": "Red",
        "CHAR-302": "Green",
    }
    for card_id, status in expected.items():
        assert report.card_results[card_id].status == status


def test_build_report_team_and_program_rollups():
    report = _build_real_report()
    assert len(report.team_rollups) == 3
    assert all(tr.status == "Red" for tr in report.team_rollups)
    assert report.program_rollup.status == "Red"
    assert any("ALPHA-202" in r for r in report.program_rollup.reasons)
    assert any("BRAVO-102" in r for r in report.program_rollup.reasons)
    assert any("CHAR-301" in r for r in report.program_rollup.reasons)


def test_build_report_feature_rollups():
    report = _build_real_report()
    statuses = {fr.feature_id: fr.status for fr in report.feature_rollups}
    assert statuses == {
        "FEAT-01": "Amber",
        "FEAT-02": "Red",
        "FEAT-03": "Red",
        "FEAT-04": "Red",
    }


def test_build_report_excludes_team_with_no_active_sprint(monkeypatch):
    teams = load_teams()
    features = load_features()
    sprints, cards = load_sprints_and_cards()
    prs = load_prs()
    risks = load_risks()

    # Simulate team_charlie having no Active sprint by monkeypatching the
    # scoping call report.py delegates to.
    import src.sprint_confidence.report as report_module
    from src.sprint_confidence.sprint_scope import scope_cards_to_active_sprints as real_scope

    def fake_scope(teams_arg, sprints_arg, cards_arg):
        real = real_scope(teams_arg, sprints_arg, cards_arg)
        filtered_cards = [c for c in real.scoped_cards if c.team_id != "team_charlie"]
        active = {k: v for k, v in real.active_sprint_id_by_team.items() if k != "team_charlie"}
        return SprintScopeResult(
            scoped_cards=filtered_cards,
            active_sprint_id_by_team=active,
            excluded_teams=real.excluded_teams + ["team_charlie"],
        )

    monkeypatch.setattr(report_module, "scope_cards_to_active_sprints", fake_scope)

    report = build_report(teams, features, sprints, cards, prs, risks, DEFAULT_THRESHOLDS, AS_OF)

    assert "team_charlie" not in report.active_sprint_id_by_team
    assert report.excluded_teams == ["team_charlie"]
    assert len(report.team_rollups) == 2
    assert any("team_charlie excluded" in r for r in report.program_rollup.reasons)


def test_render_report_contains_key_sections():
    report = _build_real_report()
    text = render_report(report)

    assert "PROGRAM STATUS: Red" in text
    assert "sprint_12" in text
    assert "sprint_09" in text
    assert "sprint_15" in text
    assert "FEAT-02 Payment Reliability: Red" in text
    assert "Team Alpha: Red" in text
    assert "ALPHA-202" in text
    assert "Quality gate failed" in text
