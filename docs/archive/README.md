# Archive — development records

These are working documents from building this project: verification
spikes, planning, drafts, and research notes. They are kept for
traceability, not as submission material. Most are written in Traditional
Chinese.

**Nothing here is required to understand or run the project.** Start with
the repository README, `docs/architecture.md`, and `docs/decision-log.md`.

| Folder / file | What it is |
|---|---|
| `tasks/` | Step-by-step execution docs for spikes S0–S9, written before each spike ran |
| `ADK-go-no-go-checklist.md` | The full ADK feasibility investigation; conclusions are summarized in `docs/decision-log.md` |
| `final-22-hours-plan.md` | The sprint plan for the last day, including its stop-loss gates |
| `devpost-submission.md` | Working draft of the Devpost submission, with revision notes |
| `demo-script.md` | Word-for-word video script, including a v1→v2 record of cutting a feature that was never built |
| `artificial-intelligence-basic-law.md` | Fact-check notes on Taiwan's AI Basic Act |
| `all-things-agentic-hackathon-summary-notes.md` | Notes and track selection analysis for the hackathon |
| `hackathon_submission_checklist.md` | Submission checklist derived from the judges' live Q&A |
| `how-to-win-the-all-things-agentic-hackathon.md` | Key takeaways, scoring rubric breakdown, and strategic insights from the official Google Cloud Live Q&A session |

## One that is worth reading

`demo-script.md` records a decision worth surfacing: the v1 script called
for a "deterministic vs model-based evaluator divergence" scene. That
feature was never built, and the submission says so. Rather than staging
it for the camera, the scene was cut and replaced with the planner's
fail-closed fallback — which is real and demonstrable. The v2 header
states the rule that produced that change: *when the script and the
implementation disagree, change the script.*
