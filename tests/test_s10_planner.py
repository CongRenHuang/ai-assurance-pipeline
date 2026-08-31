"""S10: planner.py reasoning-layer validation.

Two checks:
1. Consistency: same content, run 5x -> selection set agrees >= 80% of runs.
2. Fail-closed: planner errors (bad API key) -> selected == ALL_EVALUATORS.
"""
import json, os, pathlib
from collections import Counter

from assurance import tracing
tracing.setup(use_otlp=False)

from assurance.planner import plan_for, ALL_EVALUATORS

RESULTS = []


def rec(n, ok, d):
    RESULTS.append({"test": n, "passed": ok, "detail": d})
    print(f"{'PASS' if ok else 'FAIL'} {n}: {d}")


CONTENT = (
    "Q3 earnings release drafted from three internal analyst notes citing "
    "FY25 revenue figures."
)

# ---- 1: consistency across 5 runs ----
runs = [tuple(sorted(plan_for(CONTENT).selected)) for _ in range(5)]
counts = Counter(runs)
top_selection, top_count = counts.most_common(1)[0]
agreement = top_count / len(runs)
rec("1_selection_consistency", agreement >= 0.8,
    f"agreement={agreement:.0%} (need >=80%), most common={top_selection}, all_runs={runs}")

# ---- 2: fail-closed on planner error (bad API key forces ClientError) ----
saved_key = os.environ.get("GOOGLE_API_KEY")
os.environ["GOOGLE_API_KEY"] = "bad-key-for-fail-closed-test"
os.environ["GEMINI_API_KEY"] = "bad-key-for-fail-closed-test"
try:
    fallback_plan = plan_for(CONTENT)
finally:
    if saved_key is not None:
        os.environ["GOOGLE_API_KEY"] = saved_key
    else:
        os.environ.pop("GOOGLE_API_KEY", None)
    os.environ.pop("GEMINI_API_KEY", None)

rec("2_fail_closed_selects_all",
    sorted(fallback_plan.selected) == sorted(ALL_EVALUATORS),
    f"selected={fallback_plan.selected} (need == ALL_EVALUATORS={ALL_EVALUATORS})")
rec("2b_fallback_reasoning_says_why",
    "fallback" in fallback_plan.reasoning.lower(),
    f"reasoning={fallback_plan.reasoning[:120]}")

pathlib.Path("evidence").mkdir(exist_ok=True)
pathlib.Path("evidence/S10-results.json").write_text(
    json.dumps({"results": RESULTS}, indent=2, ensure_ascii=False, default=str),
    encoding="utf-8")
print("\nGO" if all(r["passed"] for r in RESULTS) else "\nNO-GO")
