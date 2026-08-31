# Devpost Submission Draft — Release Assessment Agent

**Created:** 2026-08-23 | **Submission Deadline:** 2026-09-01 08:00 Taipei  
**Principle:** Every number, ID, and policy identifier is derived directly from evidence files in the repo. **Not a single one was fabricated for submission.**

---

## Verified Facts (Source of Truth for All Content in This Document)

| Item | Value |
|---|---|
| Repo | `https://github.com/CongRenHuang/ai-assurance-pipeline` |
| Live URL | `https://assurance-agent-6eqpujphvq-de.a.run.app` |
| Cloud Run Revision | `assurance-agent-00005-qnc` (`--min-instances=1`, `data-residency=asia-east1`) |
| Real Assessment IDs | `ASMT-001`, `ASMT-R4-777`, `ASMT-R4-LIVE` (S8); `ASMT-001`~`ASMT-100` (Batch) |
| Policy IDs | FIN-AI-000~004 (source/egress/override) · FIN-AI-005~010 (router) · FIN-AI-011 (sovereignty) |
| Test Results | S1 6/6 · S6 6/6 · S7 8/8 · S9 12/12 · S10 Planner Concordance 100% |
| Batch Distribution | `H9 B9` invariant, `82 released` invariant (verified identical by id across 3 runs, incl. one with no API key) — AUTO/SAMPLE split within the 82 varies by run (`54/28`, `43/39`, `59/23`); 18 items require human touch, 240 → 43.2 min |
| Statutory Basis | Taiwan Artificial Intelligence Basic Act passed 3rd reading 2025-12-23; Article 18 2-year mandate |

> ✅ **Batch layer completed and rerun twice to fix corpus parameter bugs (WS5).** Then rerun a
> further two times independently (WS7/WS8) to check reproducibility. `H9`/`B9`/`82 released` are
> identical by assessment id across all three runs, including one where the planner had no API key
> at all — the AUTO/SAMPLE split *within* the 82 is not (`54/28`, `43/39`, `59/23`), because it's a
> function of which evaluators the LLM planner selects. See `evidence/S2-planner-variance.json`.
> Previous 87/9/2/2 and `24 BLOCK` versions are deprecated — 16 of the `24 BLOCK` items were due to
> a `source_ttl` generator parameter bug (`max_age_days` not aligned with `SOURCE_TTL_DAYS`), not
> designed traffic. §4 is updated with current numbers.

---

# 1. Project Name (60 character limit)

```
Release Assessment Agent
```
**24 characters.**

Alternative (if domain specialization should be explicit):
```
Release Assessment Agent for Financial AI
```
**41 characters.**

> Recommended: Use the shorter version. Including "Financial" in the title narrows the judges' perception of general applicability, whereas the elevator pitch already clarifies the domain.

---

# 2. Elevator Pitch (200 character limit)

**Primary Recommendation:**

```
When AI answers a customer's question, someone must prove why it was allowed to. This agent turns AI evidence into auditable decisions — and refuses release even when an approver says yes.
```
**186 characters.**

Alternative A (Stronger emphasis on autonomous batching):
```
An agent that reviews a queue of AI answers, decides which checks each one needs, and escalates only what needs a human — refusing release even when someone with approval authority says yes.
```
**189 characters.**

Alternative B (Shortest, sharpest):
```
A release agent for AI output in regulated work. It approves, samples, escalates, or blocks — and a human with approval authority cannot override a hard policy.
```
**158 characters.**

> **Selected: Primary Recommendation.** The first sentence establishes the scenario (someone must prove release rationale), and the second delivers the mechanism (auditability) plus a counter-intuitive hook (refusing release despite human approval). That counter-intuitive clause is why judges click through to read more.

---

# 3. Project Story (About the project)

> The following is the complete submission text ready for Devpost. All numbers are drawn from `evidence/S2-batch-run.json`.

---

## The moment this is built for

It is quarterly audit week at a bank.

An auditor points at one answer the internal AI knowledge assistant produced three months ago and asks a simple question: **"Why was this released?"**

The compliance officer opens her system. She needs, within about two minutes: which policy applied, what evidence existed at the time, who approved it — and whether anyone tried to override the decision.

Today she cannot answer that. Not because the AI was wrong, but because **nothing recorded why it was allowed to be right**.

That is the gap this project addresses. Generative AI made producing answers cheap. It did not make *approving* them cheap. The bottleneck moved from "we can't produce enough" to "we can't verify fast enough" — and verification, unlike generation, is what regulators actually ask about.

## Why now, and why this is not hypothetical

Taiwan's **Artificial Intelligence Basic Act** passed its third reading on **2025-12-23**. It establishes seven statutory principles — among them **human autonomy**, **transparency and explainability**, and **accountability**. Article 18 requires sector regulators to complete their implementing rules **within two years**.

That puts a dated, verifiable deadline on this problem: by late 2027, financial regulators in Taiwan will have concrete rules. Auditable AI approval decisions stop being a good idea and become a requirement.

*(This project does not claim regulatory compliance or certification — see Non-goals.)*

## What it does

The agent processes a queue of AI-generated answers awaiting release. For each one it:

1. **Decides which checks are warranted** — evaluation depth is tiered by risk, so a low-risk answer does not pay for a full evaluation
2. **Gathers evidence deterministically** — citation coverage, content integrity, source TTL, numeric claim consistency
3. **Routes by risk** — R0/R1 auto-release, R2 sample, R3 human review, R4 hard block
4. **Prepares an approval packet** for the few items a human must judge — conclusion, governing policy, key evidence, execution path
5. **Emits ControlEvidence** for every decision, including the trajectory it took

The human stays in the loop, but only where judgment is actually required.

## Measured on a synthetic queue

100 assessments, three independent runs (one with the planner's API key
pulled entirely). By assessment id, these are invariant across all three:

| Disposition | Count | Same items every run? |
|---|---|---|
| Escalated to human | 9 | Yes |
| Hard-blocked | 9 | Yes |
| Released (auto + sampled) | 82 | Yes, as a set |

**18 of 100 items needed a person.** Estimated review time: 240 → 43.2 minutes.

The split *within* the 82 — how many were auto-released versus sampled —
is not invariant: `54/28`, `43/39`, `59/23` across the three runs. That
boundary is a function of which evaluators the LLM planner selected; it
decides how much gets sampled for audit, never who gets escalated or
blocked. See `evidence/S2-planner-variance.json`.

*Synthetic corpus. The baseline (2.4 min/item) is an estimate documented in
`docs/baseline-estimate.md`, not a measurement — the disclaimer is assembled from a
module constant so it cannot be omitted from the output. The claim does not hinge on
the exact figure.*

## The part that surprises people

**A human with approval authority cannot override a hard policy.**

Assessment `ASMT-R4-LIVE` is a prohibited operation. Submit it to the live service with an explicit approval, and the response is:

```json
{
  "status": "BLOCKED",
  "decision": "OVERRIDE_REJECTED",
  "policy_id": "FIN-AI-004",
  "reason": "PROHIBITED operations cannot be released by any reviewer.",
  "note": "This policy does not accept human override."
}
```

The attempt itself becomes part of the audit record. This runs on the deployed Cloud Run service, not in a local mock — the evidence is committed at `evidence/S8-e2e-r4-block.json`.

## What I learned

### A correct outcome reached by the wrong path is still a bug

This was the hardest lesson, and I learned it by shipping the bug myself.

R4 was being blocked. Every test passed. The demo looked perfect. Then I read the actual execution path and found that the block came from `HardPolicyPlugin` misclassifying the request as an unregistered source — because `assess_release` has no `url` parameter, so the source lookup returned `UNKNOWN` and failed closed.

**`HardPolicyGate`'s R4 check had never executed.**

The result was right. The reason was wrong. And it would have stayed invisible, because the framework short-circuits on the first plugin that returns a value, and nothing recorded *which* plugin decided.

The fix was not another check. It was making attribution queryable: every guardrail span now carries `assurance.policy_id` **and** `assurance.plugin`, and there is an assertion (`assert_decided_by`) that fails when a policy's decision comes from the wrong component. That assertion passes on the correct path and fails on the misattributed one — while a test that only asserts `result == "BLOCKED"` passes on both.

This is why the project treats **execution trajectory as part of the evaluation contract**, not just the final result.

### Framework defaults sit on the unsafe side of the line

Three independent instances, all verified against the framework source:

| Where | Default behavior | Consequence |
|---|---|---|
| Agent-layer tool callback | stops on a **truthy** value | returning `{}` silently lets the tool run |
| Graph routing | unmatched route with no `DEFAULT` edge | logs a warning, branch ends silently — **no ControlEvidence** |
| Plugin chain | first non-`None` return short-circuits | later checks never execute |

None of these are bugs. They are reasonable defaults for general use. But each one resolves toward "quietly continue" rather than "explicitly refuse" — and for an assurance system, *silence* and *refusal* are entirely different outcomes. Only one of them leaves evidence.

**Safety was not something the framework provided. It was something I had to add on top.** I evaluated ADK's Graph Workflow for the risk router and did not use it — `route_item()` is a plain `if`/`elif` chain whose first branch rejects any unrecognized `data_class`. The fail-closed guarantee is the same; expressing it in ordinary code means it is testable without standing up the framework, and there is no silent-branch-end path to defend against.

### Evaluator independence is not free

A model-based evaluator that shares a model family with the generator is not an independent check — it is a self-confirmation loop, for the same reason you should not have code reviewed by the instance that wrote it.

I do not have a solution for this within the project's scope, so the model-based evaluator is **deferred rather than faked**. Deterministic evaluators remain the decision authority precisely because their independence is structural rather than assumed.

## How I built it

**Stack:** Gemini 3.5 Flash · Google Agent Development Kit 2.7.1 (plugins, action confirmation) · Cloud Run · OpenTelemetry with OpenInference semantic conventions · Python 3.14 · Pydantic

**Method:** Before writing production code I ran nine timeboxed verification spikes with explicit pass criteria and stop-loss conditions, deciding go/no-go on three of them. Each spike wrote its result to `evidence/` as a committed JSON artifact.

That discipline paid for itself immediately — I read the ADK source directly rather than trusting documentation, and found that the plugin layer short-circuits on `is not None` while the agent layer stops on truthiness. Placing hard policy at the plugin layer was already my plan; **the verification revealed that the reason I believed was wrong.**

Committed evidence:

| Spike | Result |
|---|---|
| S1 fail-closed plugin gate | 6/6 — includes a prompt-injection adversarial test |
| S6 hard policy override resistance | 6/6 — includes a test that **must fail** when only the result is asserted |
| S7 OpenInference decision trace | 8/8 |
| S9 trajectory assertions | 12/12 — includes the misattribution regression |

## Challenges

**Correct outcomes hiding wrong causes.** Covered above. This shaped the whole architecture.

**Deployment assumptions that only break in production.** `adk deploy cloud_run` does not bundle sibling packages, so `assurance/` never reached the container. The API's `app_name` is the folder name, not the value passed to `App(name=...)` — and session creation *silently accepted* the wrong name, with only the subsequent call returning 404. An error that is not rejected at the earliest detectable point is the expensive kind.

**Knowing what not to build.** Local model deployment, fine-tuning, a full DLP platform, a web dashboard, multi-agent orchestration — all evaluated, all documented as out of scope with reasons. A verification pipeline that quietly expands its own scope would be a poor advertisement for itself.

## Why Taskmaster

This is an autonomous multi-step workflow, not a multi-agent fleet — and that is a
design decision, not a shortfall. The system's central claim is that release
decisions belong to a deterministic policy engine rather than to a model. Adding
agents that delegate to one another would weaken exactly the property it exists to
demonstrate.

What it removes is real friction, by execution: a queue of 100 AI-generated answers
goes in, the agent decides per item which checks are warranted, gathers deterministic
evidence, routes by risk, and escalates only what needs judgment. **18 of 100 items
reached a person.** The other 82 carry committed evidence for why they did not.

Two components were built while evaluating the Fortified track and are kept because
they earn their place: the agent card at `/.well-known/agent.json` (discovery metadata
— deliberately *not* claimed as an enterprise Agent Registry) and a cross-process
approval store that survives process exit. Data sovereignty is enforced in the batch
layer only; the ADK plugin exists but is not registered in the deployed chain, and the
README says so.

**What runs where:** the `release_assessment` agent, `HardPolicyGate`, and the agent
card are deployed on Cloud Run. The 100-item batch pipeline runs locally, with its
output committed to `evidence/S2-batch-run.json`. The batch does not call the deployed
agent per item by design — the plugin-layer guarantee is already proven end-to-end by
S1/S6/S8, and routing 100 items through it would add cost without adding evidence.

## Non-goals

This is an engineering research project, not a compliance product. It does **not** provide regulatory certification or legal advice, does not use real customer data (the corpus is synthetic), and does not claim coverage of OWASP's Agentic Top 10 beyond the two items with executable test evidence: **ASI01 Agent Goal Hijack** and **ASI03 Identity & Privilege Abuse**.

Review-time figures are **estimates against a synthetic corpus**, stated as such wherever they appear.

---

**Live service:** https://assurance-agent-6eqpujphvq-de.a.run.app  
**Source:** https://github.com/CongRenHuang/ai-assurance-pipeline  

---

# 4. Data Source Traceability (Verified against artifacts)

| Appears In | Value | Source Artifact |
|---|---|---|
| §3 Measured on a synthetic queue | `H9 / B9 / 82 released` invariant, `54/28`,`43/39`,`59/23` split observed | `evidence/S2-planner-variance.json` |
| Same as above | `18` human-touched items | `HUMAN_REVIEW + BLOCK` |
| Same as above | `240 → 43.2` minutes | `assurance.metrics.render_table()` output |
| §3 Override rejection | `FIN-AI-004` / `OVERRIDE_REJECTED` | `evidence/S8-e2e-r4-block.json` |
| Fact Sheet | Planner Concordance 100% | `evidence/S10-results.json` |

> **Corpus Correction Log (WS5, 2 commits):** In the initial distribution `A39 S18 H19 B24`,
> 16 of the 24 BLOCK items originated from `make_queue.py`'s `max_age_days` not being aligned
> with `evaluators.py`'s `SOURCE_TTL_DAYS`, which was a generator parameter bug rather than designed traffic.
> The first fix (110 → 75) cleared the FAIL threshold but missed the WARN threshold (90 × 0.7 = 63d);
> the second fix (75 → 55) resolved it completely. After corrections, all 9 BLOCK items **strictly**
> trace back to intentionally planted R4 samples or SENSITIVE sovereignty blocks. The older `87/9/2/2`
> distribution never physically existed; it was an early narrative assumption.

---

# 5. Pre-submission Checklist

| Item | Status |
|---|---|
| LICENSE (Apache-2.0) | ✅ |
| Repository is Public | ✅ |
| Category selected: **The Taskmaster** | ⬜ WS8 |
| Project URL = Cloud Run Live URL | ✅ `assurance-agent-00005-qnc` |
| Cloud Run `--min-instances=1` | ✅ WS6-1 |
| `/.well-known/agent.json` accessible | ✅ WS6-1 (200 OK) |
| README first 10 lines clear and readable | ✅ WS6-2 |
| Architecture diagram | ✅ `docs/assets/architecture.png` (WS6-3) |
| 4-minute demo video (public, English captions) | ⬜ WS7 |
| Video numbers match committed evidence | ⬜ WS7 Pre-recording check |
| Set `--min-instances=0` after submission | ⬜ After WS8 |

## Honesty Checklist (Self-audit against judge inspection)

| Statement | Location | Verified Honest |
|---|---|---|
| Model-based evaluator = deferred, not faked | §3 What I learned | ✅ Demo script v2 also removed the placeholder frame |
| Routing numbers are from synthetic corpus | §3 Measured / Non-goals | ✅ |
| 2.4 min/item baseline is an estimate, not empirical | §3 + `metrics.py` constant | ✅ Structurally cannot be omitted from output |
| OWASP claims limited to ASI01 / ASI03 | §3 Non-goals | ✅ |
| No claim of legal/regulatory certification | §3 Non-goals | ✅ |
| Sovereignty plugin implemented but omitted from live chain | README "What runs where" | ✅ |
| Batch pipeline runs locally, not on Cloud Run | README + Devpost "Why Taskmaster" | ✅ Updated 2026-08-31 |
| Agent card is metadata, not an Agent Registry | Stated explicitly in both places | ✅ Updated 2026-08-31 |
| ADK Graph Workflow / DEFAULT_ROUTE not used | Architecture diagram + README + Devpost | ✅ Updated 2026-08-31 |
| ADK Graph Workflow **not in stack** | §3 Stack (term removed) | ✅ Updated 2026-08-31 |
