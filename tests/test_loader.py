"""Tests for loader — verifies the 5 mock JSON files parse into the expected
model shapes."""

from src.sprint_confidence.loader import (
    load_features,
    load_prs,
    load_risks,
    load_sprints_and_cards,
    load_teams,
)


def test_load_teams():
    teams = load_teams()
    assert len(teams) == 3
    alpha = next(t for t in teams if t.team_id == "team_alpha")
    assert alpha.active_sprint_id == "sprint_12"
    assert alpha.engineers == ["Jordan Kim", "Sam Patel"]


def test_load_features():
    features = load_features()
    assert len(features) == 4
    feat02 = next(f for f in features if f.feature_id == "FEAT-02")
    assert feat02.linked_card_ids == ["ALPHA-202"]


def test_load_sprints_and_cards():
    sprints, cards = load_sprints_and_cards()
    assert len(sprints) == 3
    assert len(cards) == 10
    card = next(c for c in cards if c.card_id == "ALPHA-204")
    assert card.linked_risk_ids == ["R-001"]
    assert card.linked_pr_id is None


def test_load_risks():
    risks = load_risks()
    assert len(risks) == 4
    r001 = next(r for r in risks if r.risk_id == "R-001")
    assert r001.linked_card_id == "ALPHA-204"
    assert r001.status == "Monitoring"


def test_load_prs():
    prs = load_prs()
    assert len(prs) == 4
    pr1001 = next(p for p in prs if p.pr_id == "PR-1001")
    assert pr1001.sonarqube_quality_gate == "fail"
    assert len(pr1001.reviewers) == 2
    assert pr1001.reviewers[0].reviewer_name == "Jordan Kim"

    pr1002 = next(p for p in prs if p.pr_id == "PR-1002")
    assert pr1002.reviewers == []
