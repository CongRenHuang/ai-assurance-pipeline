"""S2: prove SENSITIVE content never triggers an LLM call."""
import asyncio, json, pathlib
from assurance.env import load, model as get_model
load()
MODEL = get_model()

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from assurance.plugin import EgressGatePlugin, COUNTERS, reset_counters
from tests.counting_model import CountingGemini, CALLS, reset as reset_calls

RESULTS = []


async def run(prompt: str) -> str:
    reset_counters(); reset_calls()
    agent = LlmAgent(name="egress_probe", model=CountingGemini(model=MODEL),
                     instruction="You are a helpful assistant.")
    runner = InMemoryRunner(agent=agent, plugins=[EgressGatePlugin()])
    s = await runner.session_service.create_session(
        app_name=runner.app_name, user_id="s2")
    out = []
    async for ev in runner.run_async(
        user_id="s2", session_id=s.id,
        new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
    ):
        if ev.content and ev.content.parts:
            for p in ev.content.parts:
                if p.text: out.append(p.text)
    return "".join(out)


def rec(name, ok, detail):
    RESULTS.append({"test": name, "passed": ok, "detail": detail})
    print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")


async def main():
    # A. SENSITIVE -> LLM must be called 0 times
    txt = await run("[SENSITIVE] 客戶身分證 A123456789，請摘要這筆資料。")
    rec("1_llm_never_called", CALLS["generate_content"] == 0,
        f"generate_content called {CALLS['generate_content']} times (need 0)")
    rec("2_gate_triggered", COUNTERS["model_blocked"] == 1,
        f"model_blocked={COUNTERS['model_blocked']}")
    rec("3_blocked_in_output", "BLOCKED" in txt, f"output={txt[:80]!r}")

    # B. control group: normal content should call through (proves gate isn't blanket-block)
    await run("What is 2 + 2?")
    rec("4_normal_passes", CALLS["generate_content"] >= 1,
        f"generate_content called {CALLS['generate_content']} times (need >=1)")

    pathlib.Path("evidence").mkdir(exist_ok=True)
    pathlib.Path("evidence/S2-results.json").write_text(
        json.dumps(RESULTS, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nGO" if all(r["passed"] for r in RESULTS) else "\nNO-GO")


asyncio.run(main())
