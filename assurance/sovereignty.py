"""WS4-3: data sovereignty. Two integration points, same pure check:

1. Batch pipeline (assurance/batch.py) -- check_sovereignty() runs per item
   alongside route_item(), so a SENSITIVE item gets BLOCKed with evidence
   even before any evaluator runs.
2. Live agent (deploy_agent/agent.py) -- SovereigntyGatePlugin sits ahead
   of EgressGatePlugin in the plugin chain (lower plugin_index), as a
   pre-check on data_class rather than a rewrite of EgressGatePlugin's
   existing keyword-marker logic.

UNKNOWN data_class fails closed, same as the rest of this codebase.
"""
from __future__ import annotations
from typing import Any, Literal, Optional

from google.adk.plugins.base_plugin import BasePlugin

from .tracing import guardrail_span

DomainVerdict = Literal["ALLOWED", "BLOCKED"]

ALLOWED_REGION = "asia-east1"

# Which data_class may egress to an external model / leave the deployment
# region at all. v0.1: SENSITIVE never egresses, regardless of region.
DOMAIN_POLICY: dict[str, DomainVerdict] = {
    "PUBLIC": "ALLOWED",
    "INTERNAL": "ALLOWED",
    "SENSITIVE": "BLOCKED",
}

POLICY_ID = "FIN-AI-011"


def check_sovereignty(data_class: str, target_region: str = ALLOWED_REGION) -> tuple[bool, str]:
    """Returns (allowed, reason). Unknown data_class fails closed."""
    verdict = DOMAIN_POLICY.get(data_class)
    if verdict is None:
        return False, f"Unknown data_class '{data_class}'. Fail closed ({POLICY_ID})."
    if verdict == "BLOCKED":
        return False, (
            f"data_class '{data_class}' must not egress externally "
            f"(sovereignty policy {POLICY_ID}).")
    if target_region != ALLOWED_REGION:
        return False, (
            f"target_region '{target_region}' != allowed '{ALLOWED_REGION}'. "
            f"Fail closed ({POLICY_ID}).")
    return True, f"data_class '{data_class}' permitted within {ALLOWED_REGION}."


SENSITIVE_MARKER = "[SENSITIVE]"


def _extract_text(llm_request) -> str:
    chunks = []
    for c in getattr(llm_request, "contents", None) or []:
        for p in getattr(c, "parts", None) or []:
            t = getattr(p, "text", None)
            if t:
                chunks.append(t)
    return "\n".join(chunks)


class SovereigntyGatePlugin(BasePlugin):
    """Pre-check ahead of EgressGatePlugin: blocks by data_class, not by
    scanning for a wider set of sensitive-content keywords."""

    def __init__(self, plugin_index: int = 0) -> None:
        super().__init__(name="sovereignty_gate")
        self.plugin_index = plugin_index

    async def before_model_callback(self, *, callback_context, llm_request):
        from google.genai import types
        from google.adk.models.llm_response import LlmResponse

        text = _extract_text(llm_request)
        data_class = "SENSITIVE" if SENSITIVE_MARKER in text else "PUBLIC"
        allowed, reason = check_sovereignty(data_class)

        with guardrail_span(
            "policy.sovereignty",
            policy_id=POLICY_ID, risk_tier="R4" if not allowed else "R0",
            decision="BLOCK" if not allowed else "ALLOW",
            plugin="SovereigntyGatePlugin", plugin_index=self.plugin_index,
        ):
            if not allowed:
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=f"BLOCKED by {POLICY_ID}: {reason}")],
                    )
                )
            return None
