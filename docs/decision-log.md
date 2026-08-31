# Decision log

Nine timeboxed verification spikes ran before production code was written.
Each had explicit pass criteria and a stop-loss condition; three were
go/no-go gates on whether to enter the hackathon at all. Every spike wrote
its result to `evidence/` as a committed artifact.

This page records what was decided and why. The full investigation is in
`docs/archive/ADK-go-no-go-checklist.md`.

---

## 1. Hard policy goes at the plugin layer, not the agent layer

**Decision:** enforce non-overridable policy in an ADK `BasePlugin`, never
in an agent-level tool callback.

**Why:** the two layers stop the call chain on different conditions, and
the difference is not documented. Read from the ADK 2.7.1 wheel source:

| Layer | Short-circuits when | Consequence |
|---|---|---|
| Plugin (`plugins/plugin_manager.py`) | `result is not None` | an empty dict **does** block |
| Agent (`flows/llm_flows/functions.py`) | `if function_response:` (truthy) | an empty dict **does not** block — it silently passes |

A policy gate that returns an empty container fails open at the agent
layer and closed at the plugin layer. `PolicyVerdict.to_tool_response()`
carries an assertion that its payload is never empty, so the guarantee
does not depend on remembering this.

Evidence: `evidence/S1-layer-difference.txt`, `evidence/S1-results.json`.

**A note on how this was found:** the original plan put hard policy at the
plugin layer for a different reason. The verification showed the placement
was right and the reasoning was wrong.

---

## 2. The risk router is plain Python, not ADK Graph Workflow

**Decision:** `assurance/policy.py::route_item()` is an `if`/`elif` chain
whose first branch rejects any unrecognized `data_class`.

**Why:** Graph Workflow was evaluated and would have worked — routing is
deterministic and never touches the model. Two things decided against it.
Its default on an unmatched route with no `DEFAULT` edge is to log a
warning and end the branch silently, which produces no `ControlEvidence`;
defending against that means adding an explicit fallback edge anyway.
And a plain function is testable without standing up the framework, which
matters more for the component that makes every release decision.

The fail-closed guarantee is identical. The cost is that the routing is
not visible in ADK's own graph tooling.

The router is covered by the batch run itself: every one of the 100 items
in `evidence/S2-batch-run.json` carries the `policy_id` that routed it.

---

## 3. The LLM triages; it never decides

**Decision:** Gemini selects which evaluators to run. Deterministic
evaluators produce the evidence, and the policy engine decides the route.
The planner's instruction states explicitly: *you do not decide whether it
may be released.*

**Why:** a model-based evaluator sharing a model family with the generator
is not an independent check — it is a self-confirmation loop. That
component is deferred rather than approximated, and the submission says so.

**Fail-closed applies to autonomy too.** If the planner errors or returns
an empty selection, the fallback runs *all four* evaluators, not fewer.
Uncertainty buys more scrutiny.

Evidence: `evidence/S10-results.json` — selection consistency 100% at
temperature 0; fallback verified by removing the API key.

---

## 4. Execution trajectory is part of the evaluation contract

**Decision:** every guardrail span carries `assurance.policy_id` **and**
`assurance.plugin`, and `assert_decided_by` fails when a policy's decision
comes from the wrong component.

**Why:** R4 was blocking correctly and every test passed — but the block
came from `HardPolicyPlugin` misclassifying the request as an unregistered
source (`assess_release` has no `url` parameter, so the lookup returned
`UNKNOWN` and failed closed). `HardPolicyGate`'s R4 check had never run.
The result was right; the reason was wrong.

A test asserting `result == "BLOCKED"` passes on both the correct and the
misattributed path. `assert_decided_by` passes only on the correct one.

Evidence: `evidence/S6-results.json` (6/6), `evidence/S9-results.json`
(12/12, including the misattribution regression).

---

## 5. Deployment findings that only appear in production

Three issues that local testing could not surface:

- `adk deploy cloud_run` does not bundle sibling packages, so `assurance/`
  never reached the container. Deploy with `gcloud run deploy --source .`.
- The API's `app_name` is the **folder name** (`deploy_agent`), not the
  value passed to `App(name=...)`. Session creation silently accepted the
  wrong name; only the subsequent call returned 404.
- Unauthenticated access is not granted by default.

An error not rejected at the earliest detectable point is the expensive
kind. Evidence: `evidence/S8-*`.

---

## 6. Corpus parameters must be aligned with evaluator thresholds

The synthetic corpus generator drew source ages up to 110 days while the
TTL evaluator fails at 90, producing 15 blocks that were not part of the
planted design. The first fix (110→75) cleared the FAIL line but not the
WARN line at 63 days — the same bug, half fixed. The second (75→55)
cleared both.

Final distribution: `AUTO 54 · SAMPLE 28 · HUMAN_REVIEW 9 · BLOCK 9`. All
nine blocks trace to deliberately planted R4 samples or SENSITIVE
sovereignty rejections.

The generator was changed, not the evaluator: thresholds are the product
claim, corpus parameters are test input.

Evidence: `evidence/S2-batch-run.json`.

---

## What was decided not to build

| Not built | Reason |
|---|---|
| Model-based second evaluator | Not independent of the generator; deferred rather than faked |
| Multi-agent delegation | Would weaken the claim that decisions belong to a deterministic engine |
| Cloud SQL for approvals | SQLite proves cross-process persistence at no IAM cost |
| Web dashboard | Terminal output is sufficient, and polish invites doubt about substance |
| Regulatory compliance claims | This is engineering research, not a compliance product |
