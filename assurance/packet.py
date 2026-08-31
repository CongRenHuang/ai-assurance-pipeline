"""WS3-2: plain-text approval packet for one HUMAN_REVIEW / BLOCK item.

Gives the reviewer options to pick (A/B/C), not just information to read --
the packet is the interface, not a report.
"""
from __future__ import annotations
from .schema import ControlEvidence, RiskDecision

HUMAN_REVIEW_OPTIONS = [
    "A) APPROVE -- release as-is",
    "B) APPROVE WITH CONDITIONS -- release after the noted fixes",
    "C) REJECT -- do not release; escalate for rework",
]

BLOCK_OPTIONS = [
    "A) ACKNOWLEDGE BLOCK -- no override exists for this policy",
    "B) ESCALATE -- request a policy exception review (outside this tool)",
]


def _trajectory_lines(evidence: ControlEvidence) -> list[str]:
    lines = []
    for i, step in enumerate(evidence.trajectory, start=1):
        if isinstance(step, dict):
            name = step.get("step", "?")
            extras = {k: v for k, v in step.items() if k != "step"}
            extra_str = f" ({', '.join(f'{k}={v}' for k, v in extras.items())})" if extras else ""
            lines.append(f"  {i}. {name}{extra_str}")
        else:
            lines.append(f"  {i}. {step}")
    return lines


def render_packet(assessment_id: str, decision: RiskDecision,
                   evidence: ControlEvidence) -> str:
    if decision.route not in ("HUMAN_REVIEW", "BLOCK"):
        raise ValueError(
            f"render_packet is for HUMAN_REVIEW/BLOCK items only, got route={decision.route}")

    options = HUMAN_REVIEW_OPTIONS if decision.route == "HUMAN_REVIEW" else BLOCK_OPTIONS

    lines = [
        f"=== Approval Packet: {assessment_id} ===",
        "",
        f"Conclusion:  {decision.route}  (risk tier {decision.risk_tier})",
        f"Policy:      {decision.policy_id}",
        f"Reason:      {decision.reason}",
        "",
        "Trajectory:",
        *_trajectory_lines(evidence),
        "",
        "Recommended action -- choose one:",
        *[f"  {o}" for o in options],
    ]
    return "\n".join(lines)
