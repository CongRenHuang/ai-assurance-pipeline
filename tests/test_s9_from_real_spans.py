"""S9: 從 S7 的真實 span tree 抽 trajectory，而非手工構造。"""
import json, pathlib
from assurance import tracing as T
from assurance.trajectory import Trajectory

T.setup(use_otlp=False)
T.CAPTURED.clear()

with T.tracer().start_as_current_span("release_assessment") as root:
    root.set_attribute(T.SPAN_KIND, T.CHAIN)
    with T.evaluator_span("eval.citation_coverage",
                          evaluation="citation_coverage",
                          score=0.96, status="PASS"):
        pass
    with T.guardrail_span("policy.hard_block",
                          policy_id="FIN-AI-004", risk_tier="R4",
                          decision="BLOCK", override_rejected=True,
                          plugin="HardPolicyGate", plugin_index=2):
        pass

T._provider.force_flush()

traj = Trajectory.from_spans(T.CAPTURED)
print("抽出的軌跡：", traj.names)

traj.assert_mandatory_checkpoint("policy.hard_block")
traj.assert_decided_by("FIN-AI-004", "HardPolicyGate")
print("invariant 全部成立")

pathlib.Path("evidence/S9-real-spans.json").write_text(
    json.dumps(traj.to_evidence(), indent=2, ensure_ascii=False), encoding="utf-8")
print("-> evidence/S9-real-spans.json")
