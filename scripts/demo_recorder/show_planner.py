"""Prints the three planner span attributes for one queue item -- the
S2 'planner span' and 'fail-closed fallback' beats. This is
SHOT-CMD-A / SHOT-CMD-B from docs/demo-storyboard.md as an importable
function instead of a heredoc, so both prerun.py (to pick an ID) and the
live recording (to actually show it happening) run the exact same code.

    python -m scripts.demo_recorder.show_planner ASMT-034
    env -u GOOGLE_API_KEY -u GEMINI_API_KEY python -m scripts.demo_recorder.show_planner ASMT-034
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUE_PATH = ROOT / "data" / "queue.jsonl"


def show(item_id: str) -> dict:
    sys.path.insert(0, str(ROOT))
    from assurance import tracing
    tracing.setup(use_otlp=False)
    from assurance.planner import plan_for

    item = next(json.loads(l) for l in QUEUE_PATH.read_text().splitlines()
                if l.strip() and json.loads(l)["id"] == item_id)
    plan_for(item["content"])
    sp = [s for s in tracing.CAPTURED if s["name"] == "planner.plan_for"][-1]
    attrs = dict(sp["attributes"])
    print()
    for k in ("assurance.selected_evaluators", "assurance.planner_reasoning",
              "assurance.planner_fallback"):
        print(f"{k:<30} {attrs[k]}")
    print()
    return attrs


if __name__ == "__main__":
    show(sys.argv[1])
