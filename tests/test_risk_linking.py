"""Tests for risk_linking — US-11 (linked risk resolution) and the
Section 9 "linked risk since Closed" edge case."""

from src.sprint_confidence.config import DEFAULT_THRESHOLDS
from src.sprint_confidence.loader import load_risks, load_sprints_and_cards
from src.sprint_confidence.models import Card, Risk
from src.sprint_confidence.risk_linking import (
    active_high_priority_risks,
    is_active,
    linked_active_risks,
    risk_priority_bucket,
)


def _risk(**overrides) -> Risk:
    defaults = dict(
        risk_id="R-TEST",
        category="Risk",
        description="Test risk",
        owner="Owner",
        probability=3,
        impact=3,
        status="Open",
        linked_card_id="CARD-TEST",
    )
    defaults.update(overrides)
    return Risk(**defaults)


def test_risk_priority_bucket_low_medium_high():
    assert risk_priority_bucket(_risk(probability=1, impact=2), DEFAULT_THRESHOLDS) == "Low"
    assert risk_priority_bucket(_risk(probability=3, impact=4), DEFAULT_THRESHOLDS) == "Medium"
    assert risk_priority_bucket(_risk(probability=5, impact=5), DEFAULT_THRESHOLDS) == "High"


def test_risk_priority_bucket_missing_probability_defaults_to_high_risk():
    risk = _risk(category="Issue", probability=None, impact=5)
    assert risk_priority_bucket(risk, DEFAULT_THRESHOLDS) == "High"


def test_is_active_excludes_closed():
    assert is_active(_risk(status="Open")) is True
    assert is_active(_risk(status="Monitoring")) is True
    assert is_active(_risk(status="Escalated")) is True
    assert is_active(_risk(status="Closed")) is False


def test_linked_active_risks_excludes_closed_and_unknown_ids():
    card = Card(
        card_id="C-1",
        team_id="team_x",
        sprint_id="sprint_x",
        title="Card",
        priority="high",
        story_points=3,
        status="in_progress",
        feature_id="FEAT-X",
        linked_pr_id=None,
        linked_risk_ids=["R-CLOSED", "R-OPEN", "R-MISSING"],
    )
    risks_by_id = {
        "R-CLOSED": _risk(risk_id="R-CLOSED", status="Closed"),
        "R-OPEN": _risk(risk_id="R-OPEN", status="Open"),
    }
    result = linked_active_risks(card, risks_by_id, DEFAULT_THRESHOLDS)
    assert [lr.risk.risk_id for lr in result] == ["R-OPEN"]


def test_active_high_priority_risks_filters_to_high_only():
    card = Card(
        card_id="C-1",
        team_id="team_x",
        sprint_id="sprint_x",
        title="Card",
        priority="high",
        story_points=3,
        status="in_progress",
        feature_id="FEAT-X",
        linked_pr_id=None,
        linked_risk_ids=["R-LOW", "R-HIGH"],
    )
    risks_by_id = {
        "R-LOW": _risk(risk_id="R-LOW", probability=1, impact=2),
        "R-HIGH": _risk(risk_id="R-HIGH", probability=5, impact=5),
    }
    result = active_high_priority_risks(card, risks_by_id, DEFAULT_THRESHOLDS)
    assert [lr.risk.risk_id for lr in result] == ["R-HIGH"]


def test_against_real_risk_and_card_data():
    risks_by_id = {r.risk_id: r for r in load_risks()}
    _, cards = load_sprints_and_cards()
    cards_by_id = {c.card_id: c for c in cards}

    # R-001: probability 3 x impact 4 = 12 -> Medium, Monitoring (active)
    assert risk_priority_bucket(risks_by_id["R-001"], DEFAULT_THRESHOLDS) == "Medium"

    # A-002: probability 2 x impact 3 = 6 -> Low, Open (active)
    assert risk_priority_bucket(risks_by_id["A-002"], DEFAULT_THRESHOLDS) == "Low"

    # I-003: probability missing (defaults to 5) x impact 5 = 25 -> High, Escalated
    assert risk_priority_bucket(risks_by_id["I-003"], DEFAULT_THRESHOLDS) == "High"

    # D-004: probability 2 x impact 4 = 8 -> Medium, Open (active)
    assert risk_priority_bucket(risks_by_id["D-004"], DEFAULT_THRESHOLDS) == "Medium"

    # BRAVO-102 is linked to I-003 (High, active) -> hard-fail trigger for US-7
    bravo_102 = cards_by_id["BRAVO-102"]
    high_risks = active_high_priority_risks(bravo_102, risks_by_id, DEFAULT_THRESHOLDS)
    assert [lr.risk.risk_id for lr in high_risks] == ["I-003"]

    # ALPHA-204 is linked to R-001 (Medium, active) -> not a hard-fail trigger
    alpha_204 = cards_by_id["ALPHA-204"]
    assert active_high_priority_risks(alpha_204, risks_by_id, DEFAULT_THRESHOLDS) == []
    assert len(linked_active_risks(alpha_204, risks_by_id, DEFAULT_THRESHOLDS)) == 1

    # ALPHA-201 has no linked risks at all
    alpha_201 = cards_by_id["ALPHA-201"]
    assert linked_active_risks(alpha_201, risks_by_id, DEFAULT_THRESHOLDS) == []
