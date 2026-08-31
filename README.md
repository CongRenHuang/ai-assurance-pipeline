# Release Assessment Agent

Turns AI evidence into defensible release/no-release decisions for financial AI
outputs. Not governance (doesn't define policy boundaries) and not
observability (doesn't just produce signals) — this is the decision layer: it
decides what gets released, on what basis, with what evidence, and it refuses
release even when a human with approval authority says yes.

**Live:** https://assurance-agent-6eqpujphvq-de.a.run.app
**Stack:** Gemini 3.5 Flash · Google ADK 2.7.1 · Cloud Run · OpenTelemetry/OpenInference
**Category:** All Things Agentic Hackathon — The Fortified Enterprise Fleet

---

## Architecture

![Architecture diagram](docs/assets/architecture.png)

The agent runs on Cloud Run and processes a queue of AI-generated answers
awaiting release. Gemini selects which checks each item warrants;
**deterministic evaluators produce the evidence and a policy engine makes
the decision** — the model is never the decision authority. Unmatched risk
classifications fall through `DEFAULT_ROUTE` to a hard block, so an
unclassified item cannot pass silently. Every decision emits
`ControlEvidence` containing the governing policy, the execution
trajectory, and the component that made the call.

---

## Claim ↔ code path

| Claim | Code |
|---|---|
| Hard policy can't be overridden by human approval | `assurance/hard_policy.py::HardPolicyGate`, `tests/test_s6_override.py` |
| Fail-closed at every layer (unknown → most restrictive) | `assurance/policy.py::route_item`, `assurance/sovereignty.py::check_sovereignty`, `assurance/planner.py` fallback |
| LLM only triages which checks to run, never decides the outcome | `assurance/planner.py` (`EvaluationPlan`, `LlmAgent`, no tools) |
| Deterministic evidence per item | `assurance/evaluators.py` (4 pure evaluators) → `assurance/schema.py::ControlEvidence` |
| Every decision traceable to which component decided it | `assurance/tracing.py` (`guardrail_span`/`evaluator_span`), `assurance/trajectory.py::assert_decided_by` |
| Data sovereignty (SENSITIVE never egresses) | `assurance/sovereignty.py::SovereigntyGatePlugin` (batch layer: wired into `assurance/batch.py`; ADK plugin layer: written, **not yet registered** in `deploy_agent/agent.py` — see Fortified status below) |
| Cross-process human approval | `assurance/approval_store.py` (SQLite), `scripts/resolve.py` |
| Machine-readable capability/policy declaration | `scripts/gen_agent_card.py` → `/.well-known/agent.json` |

## What I learned

**A correct outcome reached by the wrong path is still a bug.** R4 was
blocking correctly, every test passed, and the demo looked done — until I
read the actual execution trajectory and found the block came from
`HardPolicyPlugin` misclassifying the request as an unregistered source
(`assess_release` has no `url` parameter, so the source lookup returned
`UNKNOWN` and failed closed), not from `HardPolicyGate`'s R4 check at all. The framework short-circuits on the
first plugin that returns non-`None`, so a wrong reason produces the same
visible result as a right one. This is why the pipeline treats trajectory
as part of the evaluation contract (`assert_decided_by`), not just the
final `result` field.

**Framework defaults sit on the unsafe side of the line.** Three
independent cases, each verified against the ADK 2.7.1 wheel source, not
docs: Agent-layer tool callbacks short-circuit on a *truthy* return (`{}`
silently passes), Graph Workflow routing logs a warning and silently ends
a branch on an unmatched route with no `DEFAULT_ROUTE`, and the Plugin
chain stops at the first non-`None` return. None of these are bugs — they
are reasonable defaults for general use. But each resolves toward "quietly
continue," so `DEFAULT_ROUTE → HardBlock` and plugin-layer enforcement
(not agent-layer) aren't nice-to-haves — they're the only way an
unclassified state fails closed instead of silently passing.

**A generator/threshold mismatch is the same bug twice if you only fix it
halfway.** The corpus generator drew random source ages up to 110 days
while the evaluator enforces a 90-day FAIL threshold — producing 15 blocks
that weren't part of the designed R2/R3/R4 sample. The first fix
(`max_age_days=75`) cleared the FAIL line but missed that `source_ttl` has
a second, lower WARN threshold at `90 × 0.7 = 63` days, so the same class
of noise resurfaced one tier down. Both fixes align the generator to a
threshold that already exists in the evaluator; neither invents a
threshold to hit a target ratio — the corpus's own docstring states counts
are not tuned, and the final distribution (`AUTO 54 · SAMPLE 28 ·
HUMAN_REVIEW 9 · BLOCK 9`) is what fell out once the mismatch was gone.

## Fortified Enterprise Fleet — honest status

| Requirement | Status |
|---|---|
| Agent card (`/.well-known/agent.json`) | **Implemented.** Generated from `policy_ids.py`, served live, verified on the deployed Cloud Run service. |
| Cross-process human approval | **Implemented.** SQLite-backed (`data/approvals.db`), verified across two independent process invocations (`escalate()` in the batch run, `resolve()` in a separate terminal). |
| Data sovereignty (SENSITIVE data never leaves the approved region) | **Partially implemented.** The pure-function check (`check_sovereignty`) and its batch-layer enforcement are live and verified against the corpus (SENSITIVE items are blocked with evidence). The ADK `SovereigntyGatePlugin` exists but is **not yet registered** in `deploy_agent/agent.py`'s live plugin chain — only `HardPolicyPlugin`, `EgressGatePlugin`, and `HardPolicyGate` are wired into the deployed agent today. |

## Run locally

```bash
uv sync
python -m assurance.batch --queue data/queue.jsonl   # end-to-end batch run
python tests/test_s10_planner.py                     # planner consistency + fail-closed
adk web spike_agent                                   # interactive dev UI
```

## Deploy

```bash
gcloud run deploy assurance-agent --source . --region=asia-east1 --min-instances=1
```

`adk deploy cloud_run` does not bundle sibling packages, so `assurance/`
never reaches the container that way — `gcloud run deploy --source .` with
the `Dockerfile` in this repo is the path that works. The REST API's
`app_name` is the folder name (`deploy_agent`), not the value passed to
`App(name=...)`.
