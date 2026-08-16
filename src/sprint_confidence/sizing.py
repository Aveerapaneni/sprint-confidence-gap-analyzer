"""US-1 and US-4: convert diff stats into a Small/Medium/Large size bucket.

Same bucket logic is applied to both the initial PR diff (US-1) and the
post-review round-2 diff (US-4), using configurable thresholds from
config.py — DEFAULT_THRESHOLDS documents the fallback cutoffs when none are
supplied (US-1 acceptance criterion).

A PR's bucket is the worse of two independent lookups — one from total
lines changed, one from files touched — since either can make a diff hard
to review even when the other looks small.
"""

from typing import Optional

from .config import Thresholds

SMALL = "Small"
MEDIUM = "Medium"
LARGE = "Large"

_ORDER = {SMALL: 0, MEDIUM: 1, LARGE: 2}


def _bucket_from_lines(total_lines: int, thresholds: Thresholds) -> str:
    if total_lines <= thresholds.size_small_max_lines:
        return SMALL
    if total_lines <= thresholds.size_medium_max_lines:
        return MEDIUM
    return LARGE


def _bucket_from_files(files_changed: int, thresholds: Thresholds) -> str:
    if files_changed <= thresholds.size_small_max_files:
        return SMALL
    if files_changed <= thresholds.size_medium_max_files:
        return MEDIUM
    return LARGE


def _worse_bucket(a: str, b: str) -> str:
    return a if _ORDER[a] >= _ORDER[b] else b


def _bucket_for(total_lines: int, files_changed: int, thresholds: Thresholds) -> str:
    return _worse_bucket(
        _bucket_from_lines(total_lines, thresholds),
        _bucket_from_files(files_changed, thresholds),
    )


def size_bucket(
    lines_added: int, lines_deleted: int, files_changed: int, thresholds: Thresholds
) -> str:
    return _bucket_for(lines_added + lines_deleted, files_changed, thresholds)


def round2_size_bucket(
    round2_lines: Optional[int], round2_files: Optional[int], thresholds: Thresholds
) -> Optional[str]:
    """Returns None when no round-2 rework has happened yet (round2_lines
    is null in the source data), distinct from a bucket of Small (round 2
    happened with a trivial/zero diff)."""
    if round2_lines is None or round2_files is None:
        return None
    return _bucket_for(round2_lines, round2_files, thresholds)
