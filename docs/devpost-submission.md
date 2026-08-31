# Devpost 提交草稿 — Release Assessment Agent

**建立：** 2026-08-23 ｜ **交件：** 2026-09-01 08:00 台北
**原則：** 每個數字、ID、政策編號都取自 repo 內的 evidence 檔案。**沒有一個是為了提交而編造的。**

---

## 🔴 先做這件事：沒有 LICENSE 檔案

`ls LICENSE*` → **NO LICENSE FILE**

Repo 是 `github.com/CongRenHuang/ai-assurance-pipeline`（public）。**提交前必須補上**，否則是失格風險。

```bash
cd ~/Project/ai-assurance-pipeline
curl -sL https://www.apache.org/licenses/LICENSE-2.0.txt -o LICENSE
# 或 GitHub UI: Add file → Create new file → 檔名輸入 LICENSE → 右側 "Choose a license template" → Apache-2.0
git add LICENSE && git commit -m "chore: add Apache-2.0 license"
```

用 GitHub 的 license template 才會被偵測並顯示在 repo 首頁 About 區塊。

---

## 已查證的事實（本文件所有內容的來源）

| 項目 | 值 |
|---|---|
| Repo | `https://github.com/CongRenHuang/ai-assurance-pipeline` |
| Live URL | `https://assurance-agent-6eqpujphvq-de.a.run.app` |
| 真實 assessment ID | `ASMT-001`, `ASMT-R4-777`, `ASMT-R4-LIVE` |
| 政策編號 | FIN-AI-000 / 001 / 002 / 003 / 004 |
| 測試結果 | S1 6/6 · S6 6/6 · S7 8/8 · S9 12/12 |
| 法源 | 人工智慧基本法 2025/12/23 三讀，第 18 條兩年期限 |

> ⚠️ **批次層（100 筆佇列、87/9/2/2 分佈、240→18 分鐘）尚未建立。**
> 本文件的 §2 與 §4 已寫成「批次完成後才填入真實數字」的形式，**留了 `<<FILL>>` 標記**。
> **不要在批次跑出來之前填任何數字。**

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

> 以下為完整 Markdown，可直接貼上。`<<FILL>>` 處等批次跑完再填。

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
2. **Gathers evidence deterministically** — citation coverage, content integrity, source registration, TTL validity
3. **Routes by risk** — R0/R1 auto-release, R2 sample, R3 human review, R4 hard block
4. **Prepares an approval packet** for the few items a human must judge — conclusion, governing policy, key evidence, execution path
5. **Emits ControlEvidence** for every decision, including the trajectory it took

The human stays in the loop, but only where judgment is actually required.

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

**Safety was not something the framework provided. It was something I had to add on top.** `DEFAULT_ROUTE → HardBlock` is not a nice-to-have; it is the reason an unclassified risk tier cannot pass silently, because the graph has no edge for it.

### Evaluator independence is not free

A model-based evaluator that shares a model family with the generator is not an independent check — it is a self-confirmation loop, for the same reason you should not have code reviewed by the instance that wrote it.

I do not have a solution for this within the project's scope, so the model-based evaluator is **deferred rather than faked**. Deterministic evaluators remain the decision authority precisely because their independence is structural rather than assumed.

## How I built it

**Stack:** Gemini 3.5 Flash · Google Agent Development Kit 2.7.1 (plugins, graph workflows, action confirmation) · Cloud Run · OpenTelemetry with OpenInference semantic conventions · Python 3.14 · Pydantic

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

## Non-goals

This is an engineering research project, not a compliance product. It does **not** provide regulatory certification or legal advice, does not use real customer data (the corpus is synthetic), and does not claim coverage of OWASP's Agentic Top 10 beyond the two items with executable test evidence: **ASI01 Agent Goal Hijack** and **ASI03 Identity & Privilege Abuse**.

Review-time figures are **estimates against a synthetic corpus**, stated as such wherever they appear.

---

**Live service:** https://assurance-agent-6eqpujphvq-de.a.run.app
**Source:** https://github.com/CongRenHuang/ai-assurance-pipeline

---

# 4. 批次完成後要填的位置

跑完 `python -m assurance.batch` 後，在 §3 的 "What it does" 之後插入一段：

```markdown
## Measured on a synthetic queue

<<FILL: 實際 N>> assessments processed in a single run:

| Disposition | Count |
|---|---|
| Auto-released | <<FILL>> |
| Sampled | <<FILL>> |
| Escalated to human | <<FILL>> |
| Hard-blocked | <<FILL>> |

Estimated review time: <<FILL>> → <<FILL>> minutes.

*Synthetic corpus. The baseline is an estimate documented in `docs/baseline-estimate.md`,
not a measurement. The sensitivity band is stated there — the claim does not hinge on the
exact figure.*
```

**規則：** 數字從 `evidence/S10-results.json` 抄，不從腳本抄。**若批次未完成，整段刪除，不要留空表格。**

---

# 5. 提交前檢查

| 項目 | 狀態 |
|---|---|
| **LICENSE 檔案（Apache-2.0）** | 🔴 **缺，必補** |
| Repo 為 public | ✅ |
| Category 選 **The Fortified Enterprise Fleet** | ⬜ |
| Project URL = Cloud Run 網址 | ✅ 已備 |
| 4 分鐘影片，公開，英文字幕 | ⬜ |
| 架構圖 | ⬜ **尚未製作** |
| Cloud Run `--min-instances=1`（8/28 調）| ⬜ |
| README 前 10 行看得懂 | ⬜ |
| 提交後 `--min-instances=0` | ⬜ |

**架構圖是提交硬性要求，目前完全沒開始。** 建議 8/30 用 Mermaid 畫，內容就是 §3 "What it does" 的五個步驟 + 四條路由。
