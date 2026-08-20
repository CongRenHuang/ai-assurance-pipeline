# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Pre-implementation validation phase for **AI Assurance Pipeline** — a deterministic-control layer for AI agents, targeting the All Things Agentic Hackathon (deadline 2026-09-01 Taipei time). No application code exists yet; this repo currently holds the Go/No-Go technical validation plan and its supporting docs. Python/uv project scaffolding (`.venv`, `.env`) is set up but `assurance/`, `spike_agent/`, `tests/` are not yet created.

**North Star:** "How do we turn AI evidence into defensible decisions?" — not governance (defining boundaries) and not observability (producing signals), but the layer that decides what gets approved, on what basis, with what evidence.

## Key documents (read in this order)

1. `docs/tasks/00-READ-FIRST.md` — corrections to the checklist below, verified against actual ADK 2.7.1 source (not docs). Read this before `ADK-go-no-go-checklist.md`.
2. `docs/ADK-go-no-go-checklist.md` — the full S0–S9 validation plan, pass/fail criteria, decision matrix.
3. `docs/tasks/S0-environment.md` + `docs/tasks/S0-PATCH-dotenv.md` — environment setup steps and a known `load_dotenv()` bug fix.
4. `docs/positioning-vs-industry.md` — competitive/positioning analysis (governance platforms vs. observability vs. this project).
5. `adk-go-no-go.md` — top-level scratch/working copy (check for drift against `docs/ADK-go-no-go-checklist.md`).

## Stack

- Python 3.14, managed with `uv` (`.venv` already created via `uv venv`)
- Google ADK 2.7.1 (`google-adk`), Gemini API (`google-genai`)
- OpenTelemetry + `openinference-instrumentation-google-adk` for tracing
- Pydantic for domain objects

## Environment setup gotcha

`load_dotenv()` (no args) fails with `AssertionError` when run via `python - <<EOF` (stdin), because `__file__` becomes the literal string `"<stdin>"` and python-dotenv's frame-walk to locate `.env` breaks. **Never run env-dependent code via heredoc/stdin** — write a real `.py` file. Once created, use `assurance/env.py` (see `docs/tasks/S0-PATCH-dotenv.md` for its contents) which locates `.env` by walking up from `cwd` instead of relying on `__file__`.

`.gitignore` must be created **before** `.env` gets a real API key in it — order matters, never commit `.env`.

## Planned structure (per S0)

```
assurance/
├── env.py             # unified .env loading (works under stdin/pytest/REPL)
├── policy.py           # pure-function policy engine (S1)
├── plugin.py           # HardPolicyPlugin — before_tool_callback / before_model_callback (S1/S2)
├── schema.py            # Pydantic domain objects: EvaluationResult, RiskDecision, ControlEvidence (S4)
└── trajectory.py         # trajectory extraction from OpenInference span tree (S9)
spike_agent/
└── agent.py             # root_agent — entry point for `adk web` / `adk deploy`
tests/
evidence/                 # per-spike output evidence (versions, otel checks, deprecation logs)
```

## Core architectural decisions (already validated by source-reading, not yet by running code)

- **Hard policy enforcement belongs in the ADK Plugin layer, not the Agent layer.** Plugin `before_tool_callback` uses `is not None` to short-circuit (empty dict `{}` blocks); Agent-layer callbacks use truthy checks (empty dict `{}` does **not** block and is a silent-bypass trap). Confirmed at `plugins/plugin_manager.py:307` vs `flows/llm_flows/functions.py:621` in the ADK wheel source.
- **Graph Workflow routing is fail-open on unmatched routes with no `DEFAULT_ROUTE` edge** — it logs a warning and silently ends the branch (no exception, no evidence). `DEFAULT_ROUTE → HardBlock` is therefore a required safety net, not an enhancement. See `workflow/_graph.py:174-181`.
- **Python graph API differs from ADK's Go docs.** Use `from google.adk.workflow import Workflow, Edge, FunctionNode, START, DEFAULT_ROUTE`; routes are set via `Edge(from_node=..., to_node=..., route=...)`, not `workflow.StringRoute(...)`.
- **Plugin tool callbacks are keyword-only**: `before_tool_callback(self, *, tool, tool_args, tool_context)` — the arg is `tool_args`, not `args`.
- Design principle for trajectory assertions (S9): **constrain invariants, not paths** — forbidden transitions, required predecessors, side-effect cardinality, mandatory checkpoints — not `actual_path == golden_path` (combinatorially infeasible).
- OWASP coverage is intentionally narrow: only **ASI01** (Agent Goal Hijack, via S1 prompt-injection test) and **ASI03** (Identity & Privilege Abuse, via S6 override-rejection test). Do not claim broader OWASP ASI Top 10 coverage. Note: "Excessive Agency" is old LLM Top 10's LLM08, not ASI09.

## Validation workflow (S0–S9)

Spikes run in dependency order; S1, S2, S6 are the GO/NO-GO decisive items (see `ADK-go-no-go-checklist.md` Part 3 decision matrix). Each spike's evidence goes in `evidence/`. When running spike scripts, always write them as real `.py` files (see dotenv gotcha above) so they persist as artifacts — the project's stated principle is "every article needs an engineering artifact," and heredoc runs leave nothing behind.

```
S0 (env, 30m) → S1★ (fail-closed plugin gate, 60m) → S2★ (egress gate, 30m) → S3 (risk router, 60m)
S4 (structured output, 60m) → S5 (human approval via REST, 90m) → S6★ (hard policy overrides human, 45m)
→ S7 (OpenInference tracing, 45m) → S8 (Cloud Run deploy, 60m) → S9★ (trajectory assertions, 60m)
```

## Conventions

- Docs and analysis prose: Traditional Chinese (ZH-TW), per existing docs in `docs/`.
- Code and commits: English (per global CLAUDE.md).
- No git repo initialized yet in this directory — if starting one, add `.gitignore` first (already present) and verify `.env` is excluded before the first commit.
