"""S1: LLM reasoning layer that recommends which evaluators to run.

This is the only place Gemini touches the batch pipeline. It does not decide
release outcomes -- that stays with the deterministic policy engine in
policy.py. Fail-closed: if the planner errors, times out, or returns an
empty selection, fall back to running every evaluator. Uncertainty about
what to check means more checks, not fewer.
"""
from __future__ import annotations
import asyncio

from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from .env import model as get_model
from .tracing import tracer

ALL_EVALUATORS = [
    "citation_coverage",
    "content_integrity",
    "source_ttl",
    "numeric_claim_check",
]


class SkippedEvaluator(BaseModel):
    evaluator: str
    reason: str


class EvaluationPlan(BaseModel):
    selected: list[str] = Field(description="Subset of ALL_EVALUATORS to run")
    reasoning: str = Field(description="Why these evaluators were chosen")
    skipped_because: list[SkippedEvaluator] = Field(
        default_factory=list,
        description="evaluators not selected, each with a one-line reason",
    )
    # Gemini Developer API rejects dict[str, str] output schemas
    # ("additionalProperties is only supported in Gemini Enterprise Agent
    # Platform mode") -- a list of {evaluator, reason} pairs is the
    # equivalent shape that survives structured-output validation.


_INSTRUCTION = f"""You are a triage planner for an AI release-assessment pipeline.

Given a piece of content to be reviewed for release, decide which of these
evaluators are relevant and should run: {ALL_EVALUATORS}

You do NOT decide whether it may be released. You only recommend which
checks are worth running; a separate deterministic policy engine makes the
actual release decision from their results.

If you are unsure whether an evaluator applies, include it -- selecting more
evaluators is always safe, skipping a relevant one is not. For every
evaluator you leave out, give a one-line reason in skipped_because.
Respond with the EvaluationPlan schema only, no prose outside it."""


def _build_agent() -> LlmAgent:
    return LlmAgent(
        name="evaluation_planner",
        model=get_model(),
        instruction=_INSTRUCTION,
        output_schema=EvaluationPlan,
        # temperature=0 for run-to-run consistency -- this is a triage
        # decision (which checks to run), not a place where variety helps.
        generate_content_config=types.GenerateContentConfig(temperature=0.0),
    )


async def _plan_for_async(content: str) -> tuple[EvaluationPlan, bool]:
    """Runs the planner agent. Returns (plan, fallback_triggered)."""
    try:
        agent = _build_agent()
        runner = InMemoryRunner(agent=agent)
        session = await runner.session_service.create_session(
            app_name=runner.app_name, user_id="planner"
        )
        chunks: list[str] = []
        async for ev in runner.run_async(
            user_id="planner",
            session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part(text=content)]),
        ):
            if ev.content and ev.content.parts:
                for p in ev.content.parts:
                    if p.text:
                        chunks.append(p.text)
        raw = "".join(chunks).strip()
        if not raw:
            raise ValueError("planner returned empty output")
        plan = EvaluationPlan.model_validate_json(raw)
        if not plan.selected:
            raise ValueError("planner selected zero evaluators")
        return plan, False
    except Exception as exc:  # noqa: BLE001 -- any planner failure is fail-closed, not fatal
        fallback_plan = EvaluationPlan(
            selected=list(ALL_EVALUATORS),
            reasoning=f"fallback: planner failed ({exc!r}); running all evaluators fail-closed.",
        )
        return fallback_plan, True


def plan_for(content: str) -> tuple[EvaluationPlan, bool]:
    """Sync entrypoint for batch.py. Records reasoning onto a span.

    Returns (plan, fallback_triggered) -- callers must propagate the
    fallback flag into their own evidence/trajectory rather than hardcode
    False, or the trajectory will contradict the planner's own reasoning.
    """
    plan, fallback = asyncio.run(_plan_for_async(content))
    with tracer().start_as_current_span("planner.plan_for") as sp:
        sp.set_attribute("assurance.selected_evaluators", plan.selected)
        sp.set_attribute("assurance.planner_reasoning", plan.reasoning[:400])
        sp.set_attribute("assurance.planner_fallback", fallback)
    return plan, fallback
