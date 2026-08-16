"""Shared date-parsing helper for the ISO 'YYYY-MM-DD' strings used
throughout the mock data (created_date, last_action_date, sprint
end_date, etc.)."""

from datetime import date


def parse_date(value: str) -> date:
    return date.fromisoformat(value)
