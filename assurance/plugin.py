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
