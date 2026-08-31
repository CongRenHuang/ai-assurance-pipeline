# Devpost 提交草稿 — Release Assessment Agent

**建立：** 2026-08-23 ｜ **交件：** 2026-09-01 08:00 台北
**原則：** 每個數字、ID、政策編號都取自 repo 內的 evidence 檔案。**沒有一個是為了提交而編造的。**

---

## 已查證的事實（本文件所有內容的來源）

| 項目 | 值 |
|---|---|
| Repo | `https://github.com/CongRenHuang/ai-assurance-pipeline` |
| Live URL | `https://assurance-agent-6eqpujphvq-de.a.run.app` |
| Cloud Run revision | `assurance-agent-00005-qnc`（`--min-instances=1`，`data-residency=asia-east1`）|
| 真實 assessment ID | `ASMT-001`, `ASMT-R4-777`, `ASMT-R4-LIVE`（S8）；`ASMT-001`~`ASMT-100`（批次）|
| 政策編號 | FIN-AI-000~004（source/egress/override）· FIN-AI-005~010（router）· FIN-AI-011（sovereignty）|
| 測試結果 | S1 6/6 · S6 6/6 · S7 8/8 · S9 12/12 · S10 planner 一致率 100% |
| 批次分佈 | `A54 S28 H9 B9`（100 筆），18 筆需人工，240→43.2 分鐘 |
| 法源 | 人工智慧基本法 2025/12/23 三讀，第 18 條兩年期限 |

> ✅ **批次層已完成並重跑兩次修正語料 bug（WS5）。** 最終分佈
> `A54 S28 H9 B9`（100 筆），240→43.2 分鐘。舊的 87/9/2/2 與
> `24 BLOCK` 版本已作廢——`24 BLOCK` 中 16 筆是 `source_ttl` 產生器
> 參數 bug（`max_age_days` 與 `SOURCE_TTL_DAYS` 未對齊），非設計流量。
> §4 已用新數字填入。

---

# 1. Project name（60 字元上限）

```
Release Assessment Agent
```
**24 字元。**

備選（若想更明確標示領域）：
```
Release Assessment Agent for Financial AI
```
**41 字元。**

> 建議用短版。長版把 "Financial" 放進標題會限縮評審對適用範圍的想像，而 elevator pitch 已經說清楚領域。

---

# 2. Elevator pitch（200 字元上限）

**主推：**

```
When AI answers a customer's question, someone must prove why it was allowed to. This agent turns AI evidence into auditable decisions — and refuses release even when an approver says yes.
```
**186 字元。**

備選 A（更強調自主批次）：
```
An agent that reviews a queue of AI answers, decides which checks each one needs, and escalates only what needs a human — refusing release even when someone with approval authority says yes.
```
**189 字元。**

備選 B（最短、最尖銳）：
```
A release agent for AI output in regulated work. It approves, samples, escalates, or blocks — and a human with approval authority cannot override a hard policy.
```
**158 字元。**

> **選主推。** 第一句給場景（有人要證明），第二句給機制（可稽核）+ 反直覺鉤子（拒絕核准）。反直覺那半句是評審點進來的理由。

---

# 3. Project Story（About the project）

> 以下為完整 Markdown，可直接貼上。**所有 `<<FILL>>` 已填完**，數字來自 `evidence/S2-batch-run.json`。

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

100 assessments processed in a single run:

| Disposition | Count |
|---|---|
| Auto-released | 54 |
| Sampled | 28 |
| Escalated to human | 9 |
| Hard-blocked | 9 |

**18 of 100 items needed a person.** Estimated review time: 240 → 43.2 minutes.

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

# 4. 數字來源對照（已填完，供查核）

| 出現在 | 值 | 來源 |
|---|---|---|
| §3 Measured on a synthetic queue | `54 / 28 / 9 / 9` | `evidence/S2-batch-run.json` → `counts` |
| 同上 | `18` human-touched | `HUMAN_REVIEW + BLOCK` |
| 同上 | `240 → 43.2` 分鐘 | `assurance.metrics.render_table()` 逐字輸出 |
| §3 override 拒絕 | `FIN-AI-004` / `OVERRIDE_REJECTED` | `evidence/S8-e2e-r4-block.json` |
| 事實表 | planner 一致率 100% | `evidence/S10-results.json` |

> **語料修正紀錄（WS5，兩次 commit）：** 初版分佈 `A39 S18 H19 B24` 中，
> 24 筆 BLOCK 有 16 筆源自 `make_queue.py` 的 `max_age_days` 與
> `evaluators.py` 的 `SOURCE_TTL_DAYS` 未對齊，屬產生器參數 bug 而非設計流量。
> 第一次修正（110→75）清掉 FAIL 線但遺漏 WARN 線（90×0.7=63d），
> 第二次（75→55）補齊。修正後 9 筆 BLOCK **全部**可追溯到刻意植入的
> R4 樣本或 SENSITIVE 主權阻擋。舊的 `87/9/2/2` 從未真實存在，是早期敘事假設。

---

# 5. 提交前檢查

| 項目 | 狀態 |
|---|---|
| LICENSE（Apache-2.0） | ✅ |
| Repo 為 public | ✅ |
| Category 選 **The Taskmaster** | ⬜ WS8 |
| Project URL = Cloud Run 網址 | ✅ `assurance-agent-00005-qnc` |
| Cloud Run `--min-instances=1` | ✅ WS6-1 |
| `/.well-known/agent.json` 可存取 | ✅ WS6-1（200 OK）|
| README 前 10 行看得懂 | ✅ WS6-2 |
| 架構圖 | ✅ `docs/assets/architecture.png`（WS6-3）|
| 4 分鐘影片，公開，英文字幕 | ⬜ WS7 |
| 影片數字與 evidence 一致 | ⬜ WS7 錄前確認 |
| 提交後 `--min-instances=0` | ⬜ 留到 WS8 之後 |

## 誠實聲明清單（評審會查，先自己對一遍）

| 聲明 | 位置 | 是否誠實 |
|---|---|---|
| model-based evaluator = deferred 非造假 | §3 What I learned | ✅ 且 demo 腳本 v2 已同步移除該畫面 |
| 分流數字為合成語料 | §3 Measured / Non-goals | ✅ |
| 2.4 min/item 為估計非實測 | §3 + `metrics.py` 常數 | ✅ 結構上不可省略 |
| OWASP 僅宣稱 ASI01 / ASI03 | §3 Non-goals | ✅ |
| 不宣稱法遵認證 | §3 Non-goals | ✅ |
| sovereignty 已寫但未接入 live chain | README「What runs where」| ✅ |
| 批次跑在本機、非 Cloud Run | README + Devpost「Why Taskmaster」| ✅ 2026-08-31 修正 |
| agent card 不是 Agent Registry | 兩處皆明寫 | ✅ 2026-08-31 修正 |
| 未使用 ADK Graph Workflow / DEFAULT_ROUTE | 架構圖 + README + Devpost | ✅ 2026-08-31 修正 |
| ADK graph workflow **未使用** | §3 Stack（已移除該詞）| ✅ 2026-08-31 修正 |

> **最後一項是今天發現的。** 架構圖與 Stack 行都曾宣稱使用 ADK Graph Workflow，
> 實際路由是 `policy.py::route_item()` 的純 Python if/elif 鏈。兩處皆已修正。
