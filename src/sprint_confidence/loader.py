"""Load and parse the 5 mock JSON files in data/ into typed model objects.

Responsible for reading teams.json, features.json, cards.json (sprints +
cards), risks.json, and prs.json, and returning them as the dataclasses
defined in models.py.
"""

import json
from pathlib import Path

from .models import Card, Feature, PullRequest, Reviewer, Risk, Sprint, Team

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_teams(data_dir: Path = DEFAULT_DATA_DIR) -> list[Team]:
    data = _read_json(data_dir / "teams.json")
    return [Team(**item) for item in data["teams"]]


def load_features(data_dir: Path = DEFAULT_DATA_DIR) -> list[Feature]:
    data = _read_json(data_dir / "features.json")
    return [Feature(**item) for item in data["features"]]


def load_sprints_and_cards(data_dir: Path = DEFAULT_DATA_DIR) -> tuple[list[Sprint], list[Card]]:
    data = _read_json(data_dir / "cards.json")
    sprints = [Sprint(**item) for item in data["sprints"]]
    cards = [Card(**item) for item in data["cards"]]
    return sprints, cards


def load_risks(data_dir: Path = DEFAULT_DATA_DIR) -> list[Risk]:
    data = _read_json(data_dir / "risks.json")
    return [Risk(**item) for item in data["risks"]]


def load_prs(data_dir: Path = DEFAULT_DATA_DIR) -> list[PullRequest]:
    data = _read_json(data_dir / "prs.json")
    prs = []
    for item in data["pull_requests"]:
        reviewers = [Reviewer(**r) for r in item["reviewers"]]
        prs.append(PullRequest(**{**item, "reviewers": reviewers}))
    return prs
