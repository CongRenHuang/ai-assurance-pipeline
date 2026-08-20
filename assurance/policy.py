"""Deterministic policy engine. No LLM, no ADK dependency. Independently testable."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Literal

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
