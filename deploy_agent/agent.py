"""Cloud Run deployment entrypoint. Wires up the S1/S2/S6 gates via App.plugins.

ADK's agent loader checks for a module-level `app` (an App instance) before
falling back to `root_agent` -- see google/adk/cli/utils/agent_loader.py.
App.plugins is the correct place to register application-wide plugins for
`adk deploy` / `adk api_server`, since deployment doesn't go through
InMemoryRunner(plugins=[...]) the way the spike tests do.

This is a separate package from spike_agent/ on purpose: spike_agent/agent.py
is a fixture for the S1/S6 tests (specific tool + callback shape those tests
assert on) and must not change under S8.
"""
from assurance.env import load, model as get_model
load()
MODEL = get_model()

from google.adk.agents import LlmAgent
from google.adk.apps.app import App

from assurance import tracing
from assurance.plugin import HardPolicyPlugin, EgressGatePlugin
from assurance.hard_policy import HardPolicyGate

tracing.setup(use_otlp=False)


def assess_release(assessment_id: str, risk_tier: str) -> dict:
    """Assess whether an AI output can be released.

    Args:
        assessment_id: Identifier of the assessment.
        risk_tier: Risk tier, one of R0 R1 R2 R3 R4.
    """
    return {"status": "ASSESSED", "assessment_id": assessment_id,
            "risk_tier": risk_tier}


def fetch_source(url: str) -> dict:
    """Fetch content from a registered source URL."""
    return {"status": "OK", "content": f"<content of {url}>"}


root_agent = LlmAgent(
    name="assurance_agent",
    model=MODEL,
    instruction=(
        "You are a Release Assessment Agent for a financial AI assurance "
        "pipeline. When asked to assess or release an assessment, call "
        "assess_release with the assessment id and risk tier. When asked "
        "to fetch a URL, call fetch_source."
    ),
    tools=[assess_release, fetch_source],
)

# `app` takes priority over `root_agent` in ADK's loader -- this is what
# `adk deploy cloud_run` / `adk api_server` actually picks up, and it's
# the only way to get HardPolicyPlugin / EgressGatePlugin / HardPolicyGate
# enforced on the hosted service instead of just in local test runners.
_PLUGIN_CLASSES = [HardPolicyPlugin, EgressGatePlugin, HardPolicyGate]
_PLUGINS = [cls(plugin_index=i) for i, cls in enumerate(_PLUGIN_CLASSES)]

app = App(
    name="assurance_agent",
    root_agent=root_agent,
    plugins=_PLUGINS,
)
