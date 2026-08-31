"""WS2-2 DoD: same input, 100 runs, evaluators.py + policy.route_item
produce byte-identical results (pure function, zero LLM)."""
import json, pathlib

from assurance import tracing
tracing.setup(use_otlp=False)

from assurance.evaluators import ALL_EVALUATORS
from assurance.policy import route_item

RESULTS = []


def rec(n, ok, d):
    RESULTS.append({"test": n, "passed": ok, "detail": d})
    print(f"{'PASS' if ok else 'FAIL'} {n}: {d}")


ITEM = {
    "id": "ASMT-DET-001",
    "content": "Q3 revenue up 12%. [DRAFT]",
    "data_class": "PUBLIC",
    "claimed_sources": ["https://example.com/a", "https://example.com/b"],
    "citations": ["https://example.com/a"],
    "reference_date": "2026-08-31",
    "source_fetched_at": {"https://example.com/a": "2026-08-01"},
    "numeric_claims": [{"claim": "revenue up 12%", "value": 12.0, "source_value": 12.0}],
}

signatures = set()
for _ in range(100):
    results = [fn(ITEM) for fn in ALL_EVALUATORS.values()]
    decision = route_item(results, ITEM["data_class"])
    signatures.add((
        tuple((r.evaluation, r.score, r.status, r.detail) for r in results),
        decision.risk_tier, decision.route, decision.policy_id, decision.reason,
    ))

rec("1_100_runs_identical", len(signatures) == 1,
    f"unique signatures={len(signatures)} (need 1)")

# also check the fail-closed default: an unrecognized data_class always BLOCKs
unknown_decision = route_item([], "TYPO_CLASS")
rec("2_unknown_data_class_fails_closed",
    unknown_decision.route == "BLOCK" and unknown_decision.risk_tier == "R4",
    f"route={unknown_decision.route} risk_tier={unknown_decision.risk_tier}")

pathlib.Path("evidence").mkdir(exist_ok=True)
pathlib.Path("evidence/S2b-evaluators-results.json").write_text(
    json.dumps({"results": RESULTS}, indent=2, ensure_ascii=False), encoding="utf-8")
print("\nGO" if all(r["passed"] for r in RESULTS) else "\nNO-GO")
