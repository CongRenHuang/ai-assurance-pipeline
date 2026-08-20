"""R4 PROHIBITED: cannot be overridden by any human approval.

Design point: this check sits at the Plugin layer, ahead of any
confirmation flow. Even if a human sends confirmed=true, execution never
reaches past this gate.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Optional

from google.adk.plugins.base_plugin import BasePlugin

PROHIBITED = {
    "R4": "FIN-AI-004: PROHIBITED operations cannot be released by any reviewer.",
}

CONTROL_EVIDENCE: list[dict[str, Any]] = []
COUNTERS = {"override_attempts": 0, "override_rejected": 0, "tool_executed": 0}


def reset() -> None:
    CONTROL_EVIDENCE.clear()
    for k in COUNTERS:
        COUNTERS[k] = 0


def _emit(control_id, result, detail, trajectory):
    ev = {
        "control_id": control_id,
        "test": "hard_policy_override_resistance",
        "result": result,
        "detail": detail,
        "trajectory": trajectory,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "transformation": {"type": "none", "reversible": None,
                           "note": "v0.1 synthetic data only"},
    }
    CONTROL_EVIDENCE.append(ev)
    return ev


class HardPolicyGate(BasePlugin):
    def __init__(self) -> None:
        super().__init__(name="hard_policy_gate")

    async def before_tool_callback(
        self, *, tool, tool_args: dict[str, Any], tool_context
    ) -> Optional[dict]:
        tier = str(tool_args.get("risk_tier", "")).upper()

        if tier in PROHIBITED:
            COUNTERS["override_attempts"] += 1
            COUNTERS["override_rejected"] += 1
            reason = PROHIBITED[tier]
            _emit("FIN-AI-004", "OVERRIDE_REJECTED", reason,
                  ["hard_policy_gate", "hard_block"])
            # non-None -> short-circuits at plugin layer, tool never executes
            return {
                "status": "BLOCKED",
                "decision": "OVERRIDE_REJECTED",
                "risk_tier": tier,
                "policy_id": "FIN-AI-004",
                "reason": reason,
                "note": "This policy does not accept human override.",
            }
        return None
