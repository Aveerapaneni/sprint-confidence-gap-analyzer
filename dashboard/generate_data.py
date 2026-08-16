"""Regenerates dashboard_data.json — the data embedded in
confidence-gap-dashboard.html — from the current mock dataset.

Run from the repo root:
    python3 dashboard/generate_data.py

Evaluates the report 2 days before every active sprint's close (2026-08-09,
all 3 sprints share the same 2026-07-28 to 2026-08-11 window), matching the
PRD's own "2-3 days before sprint close" framing. To embed the refreshed
JSON into the HTML, replace the contents of the
<script id="dashboard-data" type="application/json"> block with the
minified output of this script.
"""

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.sprint_confidence.config import DEFAULT_THRESHOLDS
from src.sprint_confidence.loader import (
    load_features,
    load_prs,
    load_risks,
    load_sprints_and_cards,
    load_teams,
)
from src.sprint_confidence.report import build_report
from src.sprint_confidence.sizing import size_bucket

AS_OF = date(2026, 8, 9)
OUTPUT_PATH = Path(__file__).resolve().parent / "dashboard_data.json"


def main() -> None:
    teams = load_teams()
    features = load_features()
    sprints, cards = load_sprints_and_cards()
    prs = load_prs()
    risks = load_risks()

    report = build_report(teams, features, sprints, cards, prs, risks, DEFAULT_THRESHOLDS, AS_OF)

    cards_by_id = {c.card_id: c for c in cards}
    prs_by_id = {p.pr_id: p for p in prs}
    team_name_by_id = {t.team_id: t.team_name for t in teams}
    velocity_by_team = {t.team_id: t.velocity for t in teams}
    sprints_by_id = {s.sprint_id: s for s in sprints}

    out = {
        "as_of": report.as_of_date.isoformat(),
        "active_sprint_id_by_team": report.active_sprint_id_by_team,
        "excluded_teams": report.excluded_teams,
        "program": {
            "status": report.program_rollup.status,
            "reasons": report.program_rollup.reasons,
        },
        "teams": [],
        "features": [
            {
                "feature_id": fr.feature_id,
                "feature_name": fr.feature_name,
                "status": fr.status,
                "reasons": fr.reasons,
            }
            for fr in report.feature_rollups
        ],
        "cards": [],
    }

    for tr in report.team_rollups:
        sprint = sprints_by_id[report.active_sprint_id_by_team[tr.team_id]]
        out["teams"].append(
            {
                "team_id": tr.team_id,
                "team_name": tr.team_name,
                "status": tr.status,
                "counts": tr.status_counts,
                "sprint_id": sprint.sprint_id,
                "sprint_goal": sprint.sprint_goal,
                "sprint_start": sprint.start_date,
                "sprint_end": sprint.end_date,
                "velocity": velocity_by_team[tr.team_id],
                "at_risk_cards": [
                    {
                        "card_id": c.card_id,
                        "title": c.title,
                        "status": c.status,
                        "reasons": c.reasons,
                    }
                    for c in tr.at_risk_cards
                ],
            }
        )

    for card_id, result in report.card_results.items():
        card = cards_by_id[card_id]
        pr = prs_by_id.get(card.linked_pr_id) if card.linked_pr_id else None
        out["cards"].append(
            {
                "card_id": card.card_id,
                "title": card.title,
                "team_id": card.team_id,
                "team_name": team_name_by_id[card.team_id],
                "feature_id": card.feature_id,
                "priority": card.priority,
                "story_points": card.story_points,
                "card_status": card.status,
                "status": result.status,
                "reasons": result.reasons,
                "pr_id": pr.pr_id if pr else None,
                "pr_state": pr.state if pr else None,
                "pr_size": (
                    size_bucket(pr.lines_added, pr.lines_deleted, pr.files_changed, DEFAULT_THRESHOLDS)
                    if pr
                    else None
                ),
                "pr_split_suggestion": result.pr_split_suggestion,
                "linked_risk_ids": card.linked_risk_ids,
            }
        )

    OUTPUT_PATH.write_text(json.dumps(out, indent=2))
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
