"""S7: 六個 assurance.* 屬性 + GUARDRAIL/EVALUATOR span kind + 誰擋的可查詢。"""
import json, pathlib
from assurance import tracing as T
from assurance.policy_ids import UNKNOWN_SOURCE, R4_PROHIBITED

RESULTS = []
def rec(n, ok, d):
    RESULTS.append({"test": n, "passed": ok, "detail": d})
    print(f"{'✅' if ok else '❌'} {n}: {d}")

T.setup(use_otlp=False)

with T.tracer().start_as_current_span("release_assessment") as root:
    root.set_attribute(T.SPAN_KIND, T.CHAIN)

    with T.evaluator_span("eval.citation_coverage",
                          evaluation="citation_coverage",
                          score=0.96, status="PASS"):
        pass

    with T.guardrail_span("policy.source_governance",
                          policy_id=UNKNOWN_SOURCE.id, risk_tier="R3",
                          decision="HUMAN_REVIEW",
                          plugin="HardPolicyPlugin", plugin_index=0):
        pass

    with T.guardrail_span("policy.hard_block",
                          policy_id=R4_PROHIBITED.id, risk_tier="R4",
                          decision="BLOCK", override_rejected=True,
                          plugin="HardPolicyGate", plugin_index=2):
        pass

T._provider.force_flush()
spans = T.CAPTURED

names = [s["name"] for s in spans]
rec("1_three_layers_present",
    all(n in names for n in
        ["eval.citation_coverage", "policy.source_governance", "release_assessment"]),
    f"spans={names}")

guard = [s for s in spans if s["attributes"].get(T.SPAN_KIND) == "GUARDRAIL"]
rec("2_guardrail_kind", len(guard) == 2, f"GUARDRAIL span 數={len(guard)}")

ev = [s for s in spans if s["attributes"].get(T.SPAN_KIND) == "EVALUATOR"]
rec("3_evaluator_kind", len(ev) == 1, f"EVALUATOR span 數={len(ev)}")

need = ["assurance.policy_id", "assurance.risk_tier",
        "assurance.decision", "assurance.override_rejected",
        "assurance.plugin", "assurance.plugin_index"]
g0 = guard[0]["attributes"] if guard else {}
rec("4_six_custom_attrs", all(k in g0 for k in need),
    f"缺少={[k for k in need if k not in g0]}")

rej = [s for s in guard if s["attributes"].get("assurance.override_rejected")]
rec("5_override_rejected_traced", len(rej) == 1,
    f"override_rejected=True 的 span 數={len(rej)}")

root_id = next((s["span_id"] for s in spans
                if s["name"] == "release_assessment"), None)
children = [s for s in spans if s["parent_id"] == root_id]
rec("6_span_tree_intact", len(children) >= 3,
    f"root 底下有 {len(children)} 個子 span（S9 從此抽 trajectory）")

r4_span = next((s for s in guard
                if s["attributes"].get("assurance.policy_id") == R4_PROHIBITED.id), None)
rec("7_guardrail_has_plugin_attr",
    r4_span is not None and "assurance.plugin" in r4_span["attributes"],
    f"r4_span={r4_span}")
rec("8_r4_blocked_by_r4_policy_not_by_source_governance",
    r4_span is not None
    and r4_span["attributes"].get("assurance.plugin") == "HardPolicyGate"
    and r4_span["attributes"].get("assurance.policy_id") == "FIN-AI-004",
    "正確結果 + 錯誤原因 = 仍然是 bug。")

pathlib.Path("evidence").mkdir(exist_ok=True)
pathlib.Path("evidence/S7-results.json").write_text(
    json.dumps({"results": RESULTS,
                "spans": [{"name": s["name"], "attributes": s["attributes"]}
                          for s in spans]},
               indent=2, ensure_ascii=False, default=str), encoding="utf-8")
print("\nPASS" if all(r["passed"] for r in RESULTS) else "\nFAIL")
