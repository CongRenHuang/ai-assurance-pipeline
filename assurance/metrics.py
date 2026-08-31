"""WS3-1: time-saved estimate. Baseline and actual are both
CONST * a real BatchResult count -- never a hardcoded total. The
disclaimer is assembled inside render_table() from module constants, so
it cannot be silently dropped by a caller that forgets to add it.

The baseline itself is an ESTIMATE, not a measurement -- see
docs/baseline-estimate.md for scope and sensitivity range.
"""
from __future__ import annotations
from dataclasses import dataclass

REVIEW_MINUTES_BASELINE_PER_ITEM = 2.4  # ESTIMATE -- docs/baseline-estimate.md
REVIEW_MINUTES_ACTUAL_PER_HUMAN_ITEM = 2.4  # ESTIMATE, same source; applied
# only to items a human actually touches (HUMAN_REVIEW + BLOCK), not the
# full queue -- that delta is where the "time saved" claim comes from.

DISCLAIMER = (
    "ESTIMATE, not a measurement: "
    f"{REVIEW_MINUTES_BASELINE_PER_ITEM} min/item has no timed-pilot backing "
    "yet. See docs/baseline-estimate.md for scope and sensitivity range."
)


@dataclass
class TimeSavedEstimate:
    total_items: int
    human_touched_items: int  # HUMAN_REVIEW + BLOCK
    baseline_minutes: float
    actual_minutes: float
    saved_minutes: float
    disclaimer: str = DISCLAIMER


def estimate(counts: dict[str, int]) -> TimeSavedEstimate:
    """counts: a BatchResult.counts dict (AUTO/SAMPLE/HUMAN_REVIEW/BLOCK)."""
    total = sum(counts.values())
    human_touched = counts.get("HUMAN_REVIEW", 0) + counts.get("BLOCK", 0)
    baseline = REVIEW_MINUTES_BASELINE_PER_ITEM * total
    actual = REVIEW_MINUTES_ACTUAL_PER_HUMAN_ITEM * human_touched
    return TimeSavedEstimate(
        total_items=total, human_touched_items=human_touched,
        baseline_minutes=baseline, actual_minutes=actual,
        saved_minutes=baseline - actual)


def render_table(counts: dict[str, int]) -> str:
    e = estimate(counts)
    lines = [
        "Release Assessment -- Time Estimate",
        "------------------------------------",
        f"Total items:                    {e.total_items}",
        f"Human-touched (review + block): {e.human_touched_items}",
        f"Baseline (manual, all items):   {e.baseline_minutes:.1f} min",
        f"Actual (human-touched only):    {e.actual_minutes:.1f} min",
        f"Estimated saved:                {e.saved_minutes:.1f} min",
        "",
        e.disclaimer,
    ]
    return "\n".join(lines)
