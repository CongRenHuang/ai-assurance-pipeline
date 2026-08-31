"""Batch runner: reads the queue, runs planner + evaluators + risk router
per item, and produces a ControlEvidence for every single one.

Deliberately does not call the release-assessment ADK agent per item --
that path (S1/S6/S8) is already proven at the plugin layer. batch.py's job
is to prove the deterministic evaluate -> route -> evidence chain runs
end-to-end over a real queue, with the LLM only in the planner's advisory
role (WS1).
"""
from __future__ import annotations
import argparse
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import approval_store
from .evaluators import ALL_EVALUATORS
from .planner import plan_for
from .policy import route_item
from .schema import ControlEvidence, RiskDecision, make_evidence
from .sovereignty import POLICY_ID as SOVEREIGNTY_POLICY_ID, check_sovereignty
from .tracing import tracer

ROUTES = ("AUTO", "SAMPLE", "HUMAN_REVIEW", "BLOCK")


@dataclass
class BatchItemResult:
    """One queue item's full outcome -- what packet.py/metrics.py consume."""
    item_id: str
    decision: RiskDecision
    evidence: ControlEvidence


@dataclass
class BatchResult:
    counts: dict[str, int] = field(default_factory=lambda: {r: 0 for r in ROUTES})
    evidence: list[ControlEvidence] = field(default_factory=list)
    items: list[BatchItemResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(self.counts.values())

    def counts_line(self) -> str:
        short = {"AUTO": "A", "SAMPLE": "S", "HUMAN_REVIEW": "H", "BLOCK": "B"}
        return " ".join(f"{short[r]}{self.counts[r]}" for r in ROUTES)


def _run_evaluators(item: dict, selected: list[str]) -> list:
    return [ALL_EVALUATORS[name](item) for name in selected if name in ALL_EVALUATORS]


def run_batch(path: str, *, emit=None, delay: float = 0.0) -> BatchResult:
    result = BatchResult()
    with open(path, encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]

    for line in lines:
        item = json.loads(line)
        with tracer().start_as_current_span("release_assessment") as root:
            root.set_attribute("openinference.span.kind", "CHAIN")
            root.set_attribute("assurance.assessment_id", item["id"])

            data_class = item.get("data_class", "UNKNOWN")
            sov_allowed, sov_reason = check_sovereignty(data_class)

            if not sov_allowed:
                # Sovereignty is a pre-check ahead of evaluation, same as
                # EgressGatePlugin blocking before the model ever runs --
                # no planner call, no evaluators, no LLM cost for a
                # SENSITIVE/unknown item that can't egress at all.
                decision = RiskDecision(
                    risk_tier="R4", route="BLOCK",
                    policy_id=SOVEREIGNTY_POLICY_ID, reason=sov_reason)
                trajectory = [
                    {"step": "policy.sovereignty", "policy_id": SOVEREIGNTY_POLICY_ID,
                     "decision": "BLOCK", "data_class": data_class},
                ]
            else:
                plan, planner_fallback = plan_for(item.get("content", ""))
                evaluations = _run_evaluators(item, plan.selected)
                decision = route_item(evaluations, data_class)

                trajectory = [
                    {"step": "policy.sovereignty", "policy_id": SOVEREIGNTY_POLICY_ID,
                     "decision": "ALLOW", "data_class": data_class},
                    {"step": "planner", "selected": plan.selected, "fallback": planner_fallback},
                    *[{"step": f"eval.{e.evaluation}", "status": e.status, "score": e.score}
                      for e in evaluations],
                    {"step": "policy.route", "policy_id": decision.policy_id,
                     "route": decision.route, "risk_tier": decision.risk_tier},
                ]

            evidence = make_evidence(
                control_id=decision.policy_id,
                result=decision.route,
                detail=decision.reason,
                trajectory=trajectory,
            )

        result.counts[decision.route] += 1
        result.evidence.append(evidence)
        result.items.append(BatchItemResult(
            item_id=item["id"], decision=decision, evidence=evidence))

        if decision.route in ("HUMAN_REVIEW", "BLOCK"):
            approval_store.escalate(
                item["id"], decision.risk_tier, decision.route,
                decision.policy_id, decision.reason)

        if emit:
            emit(item["id"], decision, result)
        if delay:
            time.sleep(delay)

    return result


def _cli_emit(item_id: str, decision, result: BatchResult) -> None:
    print(f"{item_id}  {decision.route:12s} {decision.risk_tier}  "
          f"{decision.policy_id}  {result.counts_line()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the release-assessment batch pipeline.")
    parser.add_argument("--queue", default="data/queue.jsonl")
    parser.add_argument("--delay", type=float, default=0.0,
                         help="seconds between items, for recording")
    parser.add_argument("--packet", default=None,
                         help="item id to render the approval packet for "
                              "(default: first HUMAN_REVIEW/BLOCK item)")
    args = parser.parse_args()

    result = run_batch(args.queue, emit=_cli_emit, delay=args.delay)

    print(f"\ntotal={result.total} " + result.counts_line())
    assert result.total == len(result.evidence), "every item must produce evidence"
    assert all(e.detail for e in result.evidence), "no evidence may have an empty detail"

    from .metrics import render_table
    from .packet import render_packet
    print()
    print(render_table(result.counts))

    if args.packet:
        sample = next((r for r in result.items if r.item_id == args.packet), None)
        if sample is None:
            raise SystemExit(f"--packet {args.packet!r}: no such item id in {args.queue}")
    else:
        sample = next((r for r in result.items if r.decision.route in ("HUMAN_REVIEW", "BLOCK")), None)
    # Persist the authoritative artifact BEFORE any optional presentation.
    # render_packet() rejects non-HUMAN_REVIEW/BLOCK routes, and the planner
    # is an LLM -- an item's route is not guaranteed run to run. Rendering
    # first meant one ValueError discarded the whole batch.
    Path("evidence").mkdir(exist_ok=True)
    Path("evidence/S2-batch-run.json").write_text(
        json.dumps({
            "total": result.total,
            "counts": result.counts,
            "evidence": [e.model_dump() for e in result.evidence],
        }, indent=2, ensure_ascii=False),
        encoding="utf-8")

    if sample:
        route = sample.decision.route
        if route not in ("HUMAN_REVIEW", "BLOCK"):
            print(f"\n-- {sample.item_id} routed to {route} this run; "
                  f"no approval packet (packets are for HUMAN_REVIEW/BLOCK only). "
                  f"Evidence was still written.")
        else:
            print()
            print(render_packet(sample.item_id, sample.decision, sample.evidence))


if __name__ == "__main__":
    main()
