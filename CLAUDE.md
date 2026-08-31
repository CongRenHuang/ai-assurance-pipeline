# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**Release Assessment Agent** — a deterministic-control layer that turns AI evidence into
defensible release/no-release decisions for financial AI outputs. Built for the All Things
Agentic Hackathon (Taskmaster track). Not governance (doesn't define policy boundaries) and
not observability (doesn't just produce signals) — this is the decision layer: it decides
what gets released, on what basis, with what evidence, and it refuses release even when a
human with approval authority says yes.

**Central claim:** release decisions belong to a deterministic policy engine, not a model.
Gemini only triages which checks an item warrants (`assurance/planner.py`); it never decides
the outcome. `assurance/policy.py::route_item` is the decision — everything else feeds it or
records it.

Live deploy: https://assurance-agent-6eqpujphvq-de.a.run.app

## Commands

```bash
# setup
uv venv --python 3.14 && source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env && $EDITOR .env        # Gemini API key for the planner only

# run
python -m assurance.batch --queue data/queue.jsonl   # end-to-end batch, 100 items
adk web spike_agent                                    # interactive dev UI

# test — standalone scripts, not a pytest suite; run individually from repo root
python tests/test_s1_fail_closed.py
python tests/test_s6_override.py
python tests/test_s10_planner.py
# ... test_s<N>_<area>.py for each spike; some refresh files under evidence/, check diffs before committing

# deploy — `adk deploy cloud_run` does NOT bundle sibling packages (assurance/ won't reach
# the container that way). Use gcloud with the repo's own Dockerfile:
gcloud run deploy assurance-agent --source . --region=asia-east1 --min-instances=1
```

No formatter/linter configured — match nearby style. No API key? The batch still runs
end-to-end: the planner fails closed and every item gets all four evaluators (this is the
path verified in `evidence/S10-results.json`).

## Architecture

Pipeline, in order: **sovereignty check → planner (Gemini triage) → evaluators (deterministic)
→ router → evidence**.

```
assurance/              the pipeline — no ADK dependency except plugin.py/sovereignty.py
  policy.py             risk router: evaluator results + data_class -> route  (FIN-AI-005..010)
  policy_ids.py         single source of truth for every policy id
  evaluators.py         4 pure functions, zero LLM, deterministic
  planner.py            Gemini triage: picks which evaluators to run, never decides release
  batch.py              queue runner: sovereignty -> planner -> evaluators -> route -> evidence
  hard_policy.py        HardPolicyGate — R4 refuses human override            (FIN-AI-004)
  plugin.py             HardPolicyPlugin / EgressGatePlugin                   (FIN-AI-000..003)
  sovereignty.py        data_class egress check + ADK plugin                  (FIN-AI-011)
  approval_store.py     SQLite escalation store, survives process exit
  packet.py             approval packet: gives the reviewer A/B/C options, not a report
  metrics.py            time estimate; the ESTIMATE disclaimer is a module constant
  tracing.py            OpenInference guardrail_span / evaluator_span
  trajectory.py         5 invariant assertions incl. assert_decided_by
deploy_agent/           what actually runs on Cloud Run (App + plugin chain + serve.py)
spike_agent/            local ADK experimentation, not deployed
data/                   make_queue.py (seeded generator) -> queue.jsonl (100 items, committed)
evidence/               committed JSON from every spike — every number in README/docs traces here
tests/                  S1..S10 verification scripts
docs/archive/tasks/     per-spike design notes (S0-S9), read 00-READ-FIRST.md first
scripts/                gen_agent_card.py, resolve.py — small CLI helpers
runbooks/, skills/      adk-cloud-run-deploy skill + its eval runbook
```

### Two enforcement layers, not one

- **ADK Plugin layer** (`assurance/plugin.py`, `assurance/sovereignty.py`) — `before_tool_callback`
  short-circuits on `is not None` (an empty dict `{}` still blocks). This is where hard policy
  enforcement belongs.
- **ADK Agent layer** — callbacks there use truthy checks, so an empty dict `{}` does **not**
  block. It's a silent-bypass trap; verified against ADK 2.7.1 wheel source
  (`plugins/plugin_manager.py:307` vs `flows/llm_flows/functions.py:621`), not docs. Don't put
  hard policy there.

The Plugin chain also stops at the **first non-`None` return** — a plugin that returns a wrong
reason produces the same visible block as a right one, which is why the pipeline treats
execution trajectory as part of the evaluation contract (`assurance/trajectory.py::assert_decided_by`),
not just the final `result` field.

### Fail-closed is the design principle, everywhere

Framework defaults sit on the unsafe side of the line (verified against source, not docs):
Agent-layer tool callbacks short-circuit on truthy (not `is not None`), and unmatched Graph
Workflow routes log a warning and silently end the branch. Because of this, `route_item()` is
a plain `if`/`elif` chain whose first branch rejects any unrecognized `data_class` — same
fail-closed guarantee as ADK's `DEFAULT_ROUTE`, expressed in code that's testable without the
framework. Any new routing logic should preserve this: unknown inputs take the most
restrictive path and always produce a policy ID plus evidence.

### What's deployed vs. local-only

| Component | Where it runs |
|---|---|
| `release_assessment` agent + `HardPolicyGate` (R4 override rejection) | **Deployed** on Cloud Run |
| `/.well-known/agent.json` (generated from `policy_ids.py`) | **Deployed** on Cloud Run |
| `assurance.batch` 100-item pipeline | **Local only** — `python -m assurance.batch` |
| `SovereigntyGatePlugin` | **Written, not registered** in `deploy_agent/agent.py` |

The batch pipeline deliberately doesn't call the deployed agent per item — the plugin-layer
guarantee is already proven end-to-end by S1/S6/S8, and running 100 items through it would add
LLM cost without adding evidence. Keep this split in mind before assuming a change to
`assurance/` is live — check whether it's wired into `deploy_agent/agent.py`.

### Cloud Run deploy gotchas

- `app_name` in the REST API is the folder name (`deploy_agent`), not whatever is passed to
  `App(name=...)`.
- `load_dotenv()` with no args breaks under `python - <<EOF` (stdin) because `__file__`
  becomes `"<stdin>"`. Use `assurance/env.py` (locates `.env` by walking up from `cwd`), and
  always write env-dependent code as a real `.py` file, never a heredoc.

## Conventions

- Docs/analysis prose: Traditional Chinese (ZH-TW) in `docs/`. Code and commits: English.
- Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`), optional scopes (e.g.
  `fix(data): align thresholds`). Small, imperative commits.
- Test files: `test_s<N>_<area>.py`, assertions on both the decision *and* its execution path
  (not just the final result).
- `CLAUDE-STALE.md` and `adk-go-no-go.md` at repo root are pre-implementation planning
  artifacts, kept for history — not current architecture. Prefer this file, `README.md`, and
  `docs/archive/tasks/00-READ-FIRST.md` over them.
