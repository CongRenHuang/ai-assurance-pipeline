"""Deterministic policy engine. No LLM, no ADK dependency. Independently testable."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Literal

from . import policy_ids as pid
from .schema import EvaluationResult, RiskDecision

RiskTier = Literal["R0", "R1", "R2", "R3", "R4"]

SOURCE_REGISTRY: dict[str, str] = {
    "example.com": "PUBLIC",
    "internal.corp": "INTERNAL",
}


@dataclass(frozen=True)
class PolicyVerdict:
    allowed: bool
    risk_tier: RiskTier
    policy_id: str
    reason: str

    def to_tool_response(self) -> dict[str, Any]:
        """Convert to ADK tool response.

        Never return an empty dict: agent-layer callbacks use a truthy check,
        so an empty dict is falsy and would fail-open silently. Enforced by assert.
        """
        payload = {
            "status": "BLOCKED",
            "risk_tier": self.risk_tier,
            "policy_id": self.policy_id,
            "reason": self.reason,
        }
        assert payload, "policy verdict must not be an empty container (falsy causes fail-open)"
        return payload


def classify_source(url_or_host: str | None) -> str:
    """Unregistered source is always UNKNOWN. The fail-closed starting point."""
    if not url_or_host:
        return "UNKNOWN"
    host = url_or_host.split("//")[-1].split("/")[0].lower()
    return SOURCE_REGISTRY.get(host, "UNKNOWN")


def evaluate(tool_name: str, tool_args: dict[str, Any]) -> PolicyVerdict:
    """Core verdict. Pure function: same input, same output."""
    target = tool_args.get("url") or tool_args.get("host") or ""
    data_class = classify_source(target)

    if data_class == "UNKNOWN":
        return PolicyVerdict(
            allowed=False, risk_tier="R4",
            policy_id="FIN-AI-001",
            reason=f"Unregistered source '{target or '<empty>'}' -> UNKNOWN. Fail closed.",
        )
    if data_class == "INTERNAL":
        return PolicyVerdict(
            allowed=False, risk_tier="R4",
            policy_id="FIN-AI-002",
            reason="INTERNAL data must not reach external tools.",
        )
    return PolicyVerdict(
        allowed=True, risk_tier="R0",
        policy_id="FIN-AI-000",
        reason=f"Registered PUBLIC source '{target}'.",
    )


# ---------- WS2: batch content-risk router ----------
# No ADK graph workflow here -- S3's Graph Workflow build was never
# completed (checklist items unchecked, no evidence/S3-*). This is the
# pure-Python fallback the checklist itself allows for a failed S3: same
# fail-closed guarantee (unmatched input -> BLOCK), just expressed as an
# if/elif chain instead of a DEFAULT_ROUTE edge.
KNOWN_DATA_CLASSES = ("PUBLIC", "INTERNAL", "SENSITIVE")
LOW_CONFIDENCE_THRESHOLD = 0.8


def route_item(evaluations: list[EvaluationResult], data_class: str) -> RiskDecision:
    """Deterministic risk tier + route for one queue item.

    Priority (first match wins, most restrictive first):
    unknown data_class -> FAIL -> SENSITIVE -> WARN -> low score -> clean.
    """
    if data_class not in KNOWN_DATA_CLASSES:
        return RiskDecision(
            risk_tier="R4", route="BLOCK", policy_id=pid.UNKNOWN_DATA_CLASS.id,
            reason=f"Unrecognized data_class '{data_class}'. Fail closed.")

    failed = [e for e in evaluations if e.status == "FAIL"]
    if failed:
        names = ", ".join(e.evaluation for e in failed)
        return RiskDecision(
            risk_tier="R4", route="BLOCK", policy_id=pid.EVALUATOR_FAIL.id,
            reason=f"Evaluator(s) failed: {names}.")

    if data_class == "SENSITIVE":
        return RiskDecision(
            risk_tier="R3", route="HUMAN_REVIEW", policy_id=pid.SENSITIVE_FLOOR.id,
            reason="SENSITIVE data_class floors to human review regardless of evaluator scores.")

    warned = [e for e in evaluations if e.status == "WARN"]
    if warned:
        names = ", ".join(e.evaluation for e in warned)
        return RiskDecision(
            risk_tier="R3", route="HUMAN_REVIEW", policy_id=pid.EVALUATOR_WARN.id,
            reason=f"Evaluator(s) warned: {names}.")

    min_score = min((e.score for e in evaluations), default=1.0)
    if min_score < LOW_CONFIDENCE_THRESHOLD:
        return RiskDecision(
            risk_tier="R2", route="SAMPLE", policy_id=pid.LOW_CONFIDENCE.id,
            reason=f"Lowest evaluator score {min_score:.2f} < {LOW_CONFIDENCE_THRESHOLD} -> sampled.")

    return RiskDecision(
        risk_tier="R0", route="AUTO", policy_id=pid.CLEAN_AUTO.id,
        reason="All evaluators PASS with high confidence.")
