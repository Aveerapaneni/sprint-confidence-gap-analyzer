"""Tests for card_status — US-7 (RAG status) and US-13 (reasoning), plus
the Section 9 edge cases that flow into it."""

from datetime import date

from src.sprint_confidence.card_status import (
    AMBER,
    GREEN,
    RED,
    compute_card_status,
)
from src.sprint_confidence.config import DEFAULT_THRESHOLDS, Thresholds
from src.sprint_confidence.loader import load_prs, load_risks, load_sprints_and_cards

AS_OF = date(2026, 8, 16)


def test_against_real_mock_dataset_all_ten_cards():
    """Full walkthrough of every card in the mock dataset, confirming the
    RAG status each one should land on given US-7's rules."""
    risks_by_id = {r.risk_id: r for r in load_risks()}
    prs_by_id = {p.pr_id: p for p in load_prs()}
    _, cards = load_sprints_and_cards()
    cards_by_id = {c.card_id: c for c in cards}

    expected = {
        "ALPHA-201": GREEN,  # done, no PR, no risks
        "ALPHA-202": RED,  # PR-1001: quality gate fail
        "ALPHA-203": GREEN,  # done, no PR, no risks
        "ALPHA-204": AMBER,  # no PR (in progress) + active Medium risk R-001
        "BRAVO-101": GREEN,  # done, no PR, no risks
        "BRAVO-102": RED,  # clean draft PR, but active High-priority I-003 (US-11)
        "BRAVO-103": GREEN,  # merged PR, fully approved, clean signals
        "BRAVO-104": AMBER,  # no PR (in progress) + active Low risk A-002
        "CHAR-301": RED,  # PR-1004: merge conflict
        "CHAR-302": GREEN,  # done, no PR, no risks
    }

    for card_id, expected_status in expected.items():
        card = cards_by_id[card_id]
        pr = prs_by_id.get(card.linked_pr_id) if card.linked_pr_id else None
        result = compute_card_status(card, pr, risks_by_id, DEFAULT_THRESHOLDS, AS_OF)
        assert result.status == expected_status, (
            f"{card_id}: expected {expected_status}, got {result.status} "
            f"(reasons: {result.reasons})"
        )


def test_bravo_102_reasoning_names_the_risk_even_with_clean_pr():
    """US-11 acceptance: a card with a linked open High-priority Risk/Issue
    is flagged even if its own PR signals look clean, and the link is
    shown explicitly."""
    risks_by_id = {r.risk_id: r for r in load_risks()}
    prs_by_id = {p.pr_id: p for p in load_prs()}
    _, cards = load_sprints_and_cards()
    card = next(c for c in cards if c.card_id == "BRAVO-102")
    pr = prs_by_id[card.linked_pr_id]

    result = compute_card_status(card, pr, risks_by_id, DEFAULT_THRESHOLDS, AS_OF)

    assert result.status == RED
    assert any("I-003" in reason for reason in result.reasons)
    assert any("High-priority" in reason for reason in result.reasons)


def test_alpha_202_reasoning_includes_quality_gate_and_changes_requested():
    risks_by_id = {r.risk_id: r for r in load_risks()}
    prs_by_id = {p.pr_id: p for p in load_prs()}
    _, cards = load_sprints_and_cards()
    card = next(c for c in cards if c.card_id == "ALPHA-202")
    pr = prs_by_id[card.linked_pr_id]

    result = compute_card_status(card, pr, risks_by_id, DEFAULT_THRESHOLDS, AS_OF)

    assert result.status == RED
    assert any("Quality gate failed" in r for r in result.reasons)
    assert any("Changes requested" in r for r in result.reasons)
    assert any("needs re-review" in r for r in result.reasons)


def test_char_301_reasoning_includes_merge_conflict_and_pending_review():
    risks_by_id = {r.risk_id: r for r in load_risks()}
    prs_by_id = {p.pr_id: p for p in load_prs()}
    _, cards = load_sprints_and_cards()
    card = next(c for c in cards if c.card_id == "CHAR-301")
    pr = prs_by_id[card.linked_pr_id]

    result = compute_card_status(card, pr, risks_by_id, DEFAULT_THRESHOLDS, AS_OF)

    assert result.status == RED
    assert any("Merge conflict" in r for r in result.reasons)
    assert any("pending" in r.lower() for r in result.reasons)
    assert any("D-004" in r for r in result.reasons)


def test_green_card_has_no_reasons():
    risks_by_id = {r.risk_id: r for r in load_risks()}
    _, cards = load_sprints_and_cards()
    card = next(c for c in cards if c.card_id == "BRAVO-101")

    result = compute_card_status(card, None, risks_by_id, DEFAULT_THRESHOLDS, AS_OF)

    assert result.status == GREEN
    assert result.reasons == []


def test_no_pr_yet_flag_only_applies_when_card_not_done():
    risks_by_id = {r.risk_id: r for r in load_risks()}
    _, cards = load_sprints_and_cards()
    cards_by_id = {c.card_id: c for c in cards}

    # ALPHA-201 is done with no PR -> no "work not started" flag, Green.
    done_card = cards_by_id["ALPHA-201"]
    done_result = compute_card_status(done_card, None, risks_by_id, DEFAULT_THRESHOLDS, AS_OF)
    assert done_result.status == GREEN
    assert not any("work not started" in r for r in done_result.reasons)

    # ALPHA-204 is in_progress with no PR -> flagged.
    in_progress_card = cards_by_id["ALPHA-204"]
    in_progress_result = compute_card_status(
        in_progress_card, None, risks_by_id, DEFAULT_THRESHOLDS, AS_OF
    )
    assert any("work not started" in r for r in in_progress_result.reasons)


def test_pr_split_suggestion_surfaced_when_large_and_at_risk():
    risks_by_id = {r.risk_id: r for r in load_risks()}
    prs_by_id = {p.pr_id: p for p in load_prs()}
    _, cards = load_sprints_and_cards()
    card = next(c for c in cards if c.card_id == "ALPHA-202")
    pr = prs_by_id[card.linked_pr_id]

    tight = Thresholds(size_small_max_lines=100, size_medium_max_lines=300)
    result = compute_card_status(
        card, pr, risks_by_id, tight, AS_OF, sprint_end_date=date(2026, 8, 18)
    )

    assert result.status == RED
    assert result.pr_split_suggestion is not None
    assert "PR-1001" in result.pr_split_suggestion


def test_pr_split_suggestion_none_for_green_card():
    risks_by_id = {r.risk_id: r for r in load_risks()}
    prs_by_id = {p.pr_id: p for p in load_prs()}
    _, cards = load_sprints_and_cards()
    card = next(c for c in cards if c.card_id == "BRAVO-103")
    pr = prs_by_id[card.linked_pr_id]

    result = compute_card_status(
        card, pr, risks_by_id, DEFAULT_THRESHOLDS, AS_OF, sprint_end_date=date(2026, 8, 18)
    )

    assert result.status == GREEN
    assert result.pr_split_suggestion is None
