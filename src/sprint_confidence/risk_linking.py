"""US-11: resolve a card's linked_risk_ids into active, high-priority risk flags.

A card with a linked open High-priority Risk/Issue is flagged even if its
own PR signals look clean. Risks with status "Closed" are excluded from
active risk flagging (Section 9). Priority bucket is calculated from
probability x impact, same logic as the RAID Log Automator.
"""

from dataclasses import dataclass

from .config import Thresholds
from .models import Card, Risk

LOW = "Low"
MEDIUM = "Medium"
HIGH = "High"

CLOSED_STATUS = "Closed"

# Missing probability is treated as maximum (5) rather than assumed
# benign — mirrors the "never assumed to pass" rule for missing SonarQube
# data (Section 9). This mainly affects "Issue" category risks, which
# represent an already-realized problem rather than a future probability,
# so RAID logs often leave probability blank for them.
_DEFAULT_PROBABILITY_WHEN_MISSING = 5


def risk_priority_bucket(risk: Risk, thresholds: Thresholds) -> str:
    probability = (
        risk.probability if risk.probability is not None else _DEFAULT_PROBABILITY_WHEN_MISSING
    )
    score = probability * risk.impact
    if score <= thresholds.risk_low_max_score:
        return LOW
    if score <= thresholds.risk_medium_max_score:
        return MEDIUM
    return HIGH


def is_active(risk: Risk) -> bool:
    return risk.status != CLOSED_STATUS


@dataclass
class LinkedRisk:
    risk: Risk
    priority: str


def linked_active_risks(
    card: Card, risks_by_id: dict[str, Risk], thresholds: Thresholds
) -> list[LinkedRisk]:
    """All of the card's linked risks that are still active (not Closed),
    each with its calculated priority bucket. US-11 requires the link
    shown explicitly in output — callers surface risk_id/description from
    the returned Risk objects."""
    result = []
    for risk_id in card.linked_risk_ids:
        risk = risks_by_id.get(risk_id)
        if risk is None or not is_active(risk):
            continue
        result.append(LinkedRisk(risk=risk, priority=risk_priority_bucket(risk, thresholds)))
    return result


def active_high_priority_risks(
    card: Card, risks_by_id: dict[str, Risk], thresholds: Thresholds
) -> list[LinkedRisk]:
    """US-7's hard-fail trigger: active linked risks/issues at High priority."""
    return [lr for lr in linked_active_risks(card, risks_by_id, thresholds) if lr.priority == HIGH]
