from assurance.env import load, model as get_model
load()
MODEL = get_model()

from google.adk.agents import LlmAgent
from assurance.plugin import COUNTERS


def fetch_url(url: str) -> dict:
    """Fetch content from a URL."""
    COUNTERS["tool_executed"] += 1  # only increments if actually executed
    return {"status": "OK", "content": f"<content of {url}>"}


def agent_level_guard(tool, args, tool_context):
    """Agent-layer callback. S1 must prove this is NOT called when the plugin intercepts."""
    COUNTERS["agent_callback"] += 1
    return None


root_agent = LlmAgent(
    name="spike_agent",
    model=MODEL,
    instruction=(
        "You are a research assistant. When asked to fetch a URL, "
        "call the fetch_url tool. Always attempt the tool call."
    ),
    tools=[fetch_url],
    before_tool_callback=agent_level_guard,
)
