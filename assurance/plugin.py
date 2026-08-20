"""Plugin-layer hard policy. Registered on the Runner, runs before all agent callbacks."""
from __future__ import annotations
from typing import Any, Optional

from google.adk.plugins.base_plugin import BasePlugin
from .policy import evaluate

# Observation counters: S1 uses these to prove the tool truly did not execute.
COUNTERS: dict[str, int] = {
    "plugin_callback": 0,
    "agent_callback": 0,
    "tool_executed": 0,
    "blocked": 0,
    "model_callback": 0,
    "model_blocked": 0,
}


def reset_counters() -> None:
    for k in COUNTERS:
        COUNTERS[k] = 0


class HardPolicyPlugin(BasePlugin):
    """Hard policy gate that cannot be bypassed at the agent layer."""

    def __init__(self) -> None:
        super().__init__(name="hard_policy")

    async def before_tool_callback(
        self, *, tool, tool_args: dict[str, Any], tool_context
    ) -> Optional[dict]:
        # keyword-only param; must be named tool_args, not args
        COUNTERS["plugin_callback"] += 1
        verdict = evaluate(tool.name, tool_args)
        if not verdict.allowed:
            COUNTERS["blocked"] += 1
            return verdict.to_tool_response()  # non-None -> short-circuits at plugin layer
        return None  # allow, continue downstream


# ---------- S2: Egress Gate ----------
SENSITIVE_MARKERS = ("[SENSITIVE]", "身分證", "帳號", "CONFIDENTIAL")


def _extract_text(llm_request) -> str:
    """Extract all text from an LlmRequest, for sensitive-marker detection."""
    chunks = []
    for c in getattr(llm_request, "contents", None) or []:
        for p in getattr(c, "parts", None) or []:
            t = getattr(p, "text", None)
            if t:
                chunks.append(t)
    return "\n".join(chunks)


class EgressGatePlugin(BasePlugin):
    """Blocks SENSITIVE content from reaching an external model."""

    def __init__(self) -> None:
        super().__init__(name="egress_gate")

    async def before_model_callback(self, *, callback_context, llm_request):
        # ADK 2.7.1 requires Optional[LlmResponse], not Optional[Content] --
        # docs/checklist describes an older API shape (see 陷阱3 version drift).
        from google.genai import types
        from google.adk.models.llm_response import LlmResponse

        COUNTERS["model_callback"] += 1
        text = _extract_text(llm_request)
        hit = [m for m in SENSITIVE_MARKERS if m in text]
        if hit:
            COUNTERS["model_blocked"] += 1
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=(
                        "BLOCKED by FIN-AI-003: sensitive content must not be sent "
                        f"to an external model. markers={hit}"
                    ))],
                )
            )
        return None
