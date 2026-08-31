# 4 分鐘 Demo 影片逐字腳本

**專案：** Release Assessment Agent
**用途：** All Things Agentic 提交（4 分鐘上限、需含 GCP 部署證明、英文或英文字幕）
**版本：** v2 — 2026-08-31（WS5 語料修正後校準；移除未實作功能）
**規則：** 這份腳本是**規格**，但規格要跟著實作走。v1 寫於功能尚未建成時，
其中「雙路徑交叉比對」與 `source_governance` evaluator **從未實作**，v2 已移除。
**畫面上每個數字、ID、欄位都必須能在 `evidence/` 或 `data/` 搜到。**

---

## 語速與時間預算

英文口說約 **140 words/min**。4 分鐘 ≈ **560 words 上限**。
本腳本旁白約 **520 words**，留 40 words 緩衝給停頓與畫面轉場。

**每一段都標了字數。錄的時候如果某段超時，砍字不要加速。**

---

## 段落配置（對應評分權重）

| 時間 | 段落 | 主要對應 |
|---|---|---|
| 0:00–0:35 | 問題與佇列 | 建立 agent 印象 |
| 0:35–1:35 | agent 自主處理 | **Innovation 40%** |
| 1:35–2:20 | 硬性政策不可覆寫 | Architecture 30% |
| 2:20–3:05 | 核准包 | **Innovation 40%** |
| 3:05–3:35 | 摩擦力數字 | **Innovation 40%** |
| 3:35–4:00 | 雲端實跑 | **Demo/Production 30%** |

---

# 腳本

## 【0:00–0:35】問題與佇列 ｜ 78 words

**畫面**
- 0:00 標題卡（3 秒）：`Release Assessment Agent` / 副標 `Turning AI evidence into defensible decisions`
- 0:04 終端機，游標閃爍
- 0:08 執行 `python -m assurance.batch --queue data/queue.jsonl`
- 0:12 螢幕滾出 100 筆待審佇列，快速捲動
- 0:25 捲動停止，畫面停在 `100 assessments pending review`

**旁白**

> Generative AI made producing answers cheap.
> It did not make *approving* them cheap.
>
> This is a queue of one hundred AI-generated answers from a bank's internal knowledge assistant.
> Today, a compliance reviewer reads every one of them before any can be released.
>
> That's the bottleneck. Not generation — verification.
>
> Let's give the queue to the agent.

**製作備註**
- 佇列捲動要**快**，製造「這很多」的體感
- 不要念佇列內容，讓畫面說話

---

## 【0:35–1:35】agent 自主處理 ｜ 132 words ★ 最重要的一分鐘

**畫面**
- 0:35 agent 開始跑，逐筆輸出，**不要加速播放**（真實速度才可信）
- 0:45 畫面切半：左邊處理進度，右邊 **live 分流計數器**跳動
- 1:00 停在某一筆，highlight planner 的 evaluator 選擇（真實 span 屬性）：
  ```
  assurance.selected_evaluators  ["citation_coverage", "source_ttl"]
  assurance.planner_reasoning    "no numeric claims present; ..."
  assurance.planner_fallback     false
  ```
- 1:15 切到 planner **失敗時**的畫面（拔掉 API key 重跑一筆）：
  ```
  assurance.planner_fallback     true
  assurance.selected_evaluators  ["citation_coverage", "content_integrity",
                                  "source_ttl", "numeric_claim_check"]
  ```
- 1:25 highlight `fallback: true` 那一行
- 1:30 回到總覽，四類計數定格

**旁白**

> The agent doesn't run a fixed pipeline.
> For each item, a Gemini planner decides which checks are warranted — here it selected citation coverage and source TTL, and skipped the numeric check because this answer makes no numeric claim.
>
> The planner advises. It never decides whether an answer may be released.
>
> And when the planner fails — here I've pulled its API key — it does not fall back to fewer checks.
> It falls back to *all* of them. Uncertainty means more scrutiny, not less.
>
> One hundred items. Four outcomes. No human has read anything yet.

**製作備註**
- **1:15 的 fail-closed fallback 是本片第二強的畫面。** 這是真的，且是評審在意的「自主性也套用 fail-closed」
- 「not less」後面停 1 拍
- 計數器最終定格：`AUTO 54 · SAMPLE 28 · HUMAN 9 · BLOCK 9`
- ⚠️ v1 這段原本寫「deterministic vs model-based 雙路徑分歧」——**該功能從未實作**，
  且 Devpost §3 已誠實聲明 model-based evaluator 是 deferred。不可上鏡。

---

## 【1:35–2:20】硬性政策不可覆寫 ｜ 96 words ★ 本片最強的 45 秒

**畫面**
- 1:35 zoom 到 BLOCK 那 9 筆其中一筆，接著切到 live 服務的 `ASMT-R4-LIVE`
- 1:42 **切到 reviewer 視角**，畫面上有一個 APPROVE 按鈕
- 1:48 游標移過去，**按下 APPROVE**（動作要慢，讓觀眾看清楚）
- 1:52 系統回應：紅底 `BLOCKED — OVERRIDE_REJECTED`
- 2:00 切到 ControlEvidence JSON，highlight 三行：
  ```
  "decision":  "OVERRIDE_REJECTED"
  "policy_id": "FIN-AI-004"
  "trajectory": ["hard_policy_gate", "hard_block"]
  ```
- 2:12 停在 trajectory 那一行

**旁白**

> Nine were blocked outright.
> This one is a prohibited operation.
>
> I have approval authority. Watch.
>
> *(按下 APPROVE，停 2 秒，不說話)*
>
> The system still refused.
> This policy does not accept human override — and the attempt is now part of the record.
>
> Note the trajectory. It proves this block came from the R4 policy gate, not from some earlier check that happened to fire.
> A correct outcome reached by the wrong path is still a bug.

**製作備註**
- **按下 APPROVE 後必須停 2 秒不說話。** 讓觀眾自己反應過來
- 最後那句 "A correct outcome reached by the wrong path is still a bug" 是全片金句，念慢

---

## 【2:20–3:05】核准包 ｜ 104 words

**畫面**
- 2:20 切到 HUMAN_REVIEW 那 9 筆
- 2:25 顯示核准包（`packet.py` 真實輸出，勿重打）：
  ```
  === Approval Packet: ASMT-088 ===

  Conclusion:  HUMAN_REVIEW  (risk tier R3)
  Policy:      FIN-AI-008
  Reason:      Evaluator(s) warned: citation_coverage.

  Trajectory:
    1. policy.sovereignty (policy_id=FIN-AI-011, decision=ALLOW, data_class=PUBLIC)
    2. planner (selected=[...], fallback=False)
    3. eval.citation_coverage (status=WARN, score=0.667)
    4. policy.route (policy_id=FIN-AI-008, route=HUMAN_REVIEW, risk_tier=R3)

  Recommended action -- choose one:
    A) APPROVE -- release as-is
    B) APPROVE WITH CONDITIONS -- release after the noted fixes
    C) REJECT -- do not release; escalate for rework
  ```
- 2:50 reviewer 快速掃過、選一個選項
- 3:00 該筆狀態變更，approval_store 更新

**旁白**

> The nine escalated items don't arrive as raw output.
> The agent prepares a packet: what it concluded, which policy applies, the evidence that mattered, and the path it took to get there.
>
> The reviewer isn't reading an AI answer from scratch.
> They're picking one of three options against a decision the agent has already justified.
>
> That's the shift. The human stays in the loop, but only where judgment is actually required.

**製作備註**
- 核准包**不要做成漂亮網頁**。終端機或極簡卡片就好——花俏會讓評審懷疑內容
- 「in about thirty seconds」是誠實的估計，不要說「instantly」

---

## 【3:05–3:35】摩擦力數字 ｜ 82 words

**畫面**
- 3:05 切到指標畫面（終端表格即可）：
  ```
  Release Assessment -- Time Estimate
  ------------------------------------
  Total items:                    100
  Human-touched (review + block):  18
  Baseline (manual, all items):   240.0 min
  Actual (human-touched only):     43.2 min
  Estimated saved:                196.8 min

  ESTIMATE, not a measurement: 2.4 min/item has no timed-pilot
  backing yet. See docs/baseline-estimate.md for scope and
  sensitivity range.
  ```
  > 這是 `assurance.metrics.render_table()` 的**逐字輸出**，免責聲明由模組常數組出。
  > 拍攝時直接跑指令，不要重打。
- 3:25 highlight `240 → 43.2`

**旁白**

> Here's the whole batch.
> Fifty-four auto-approved, each with audit evidence. Twenty-eight sampled. Nine escalated. Nine blocked.
>
> Eighteen of a hundred items need a person. Estimated review time drops from four hours to forty-three minutes.
>
> This is a synthetic corpus and the baseline is an estimate — both are stated on screen.
> The point isn't the exact number. It's that the number exists at all, and every one of those fifty-four approvals can be audited.

**製作備註**
- ★ **誠實聲明必須留在畫面上至少 5 秒**，而且旁白要念出來
- 這一段是評審判斷你可不可信的地方。**不要美化**

---

## 【3:35–4:00】雲端實跑 ｜ 68 words

**畫面**
- 3:35 瀏覽器，網址列打出 Cloud Run URL（**要看得到 `.run.app`**）
- 3:42 送出一個 R4 請求
- 3:48 回傳 `OVERRIDE_REJECTED`
- 3:52 切到 trace viewer：GUARDRAIL / EVALUATOR span 樹
- 3:56 結束卡：專案名 + GitHub URL

**旁白**

> Everything you just saw runs on Google Cloud Run, built with Gemini and the Agent Development Kit.
>
> Here it is live — same prohibited request, same refusal.
>
> Every decision emits an OpenTelemetry trace, with policy checks tagged as guardrail spans, so an auditor can query not just what the agent decided, but which control made the decision.
>
> Evidence, not assurances.

**製作備註**
- URL 一定要入鏡，這是 GCP 部署證明
- 最後一句 "Evidence, not assurances" 是收尾，念完停 2 秒再結束

---

# Demo 需要哪些功能

## ✅ 必做（腳本直接依賴，缺一段就拍不成）

> **2026-08-31 更新：全部十項皆已完成或已移除。** 下表是拍攝前的存在性檢查清單。

| # | 功能 | 出現時間 | 狀態 | 驗證方式 |
|---|---|---|---|---|
| 1 | **批次 runner**（100 筆佇列）| 0:08–1:35 | ✅ | `python -m assurance.batch --queue data/queue.jsonl` |
| 2 | **四類分流計數** | 1:30, 3:05 | ✅ | `evidence/S2-batch-run.json` → `counts` |
| 3 | **每筆 ControlEvidence** | 2:00, 3:10 | ✅ | 同上 → `evidence` 陣列 100 筆 |
| 4 | **planner evaluator 選擇 + 理由** | 1:00 | ✅ | `evidence/S10-results.json`，一致率 100% |
| 5 | ~~雙路徑交叉比對 + 分歧升級~~ | — | ❌ **已移除** | **從未實作**；Devpost §3 已聲明 deferred |
| 5' | **planner fail-closed fallback** | 1:15 | ✅ | 拔 API key → `selected == ALL`，`fallback=true` |
| 6 | **R4 + 人工核准被拒** | 1:35–2:20 | ✅ | `evidence/S8-e2e-r4-block.json` |
| 7 | **trajectory 在 evidence 裡** | 2:00 | ✅ | 同上 → `trajectory` 欄位 |
| 8 | **核准包產生器** | 2:25 | ✅ | `assurance/packet.py::render_packet()` |
| 9 | **指標表格**（含誠實聲明）| 3:05 | ✅ | `assurance.metrics.render_table()` |
| 10 | **Cloud Run 可存取 + trace viewer** | 3:35 | ✅ | `assurance-agent-00005-qnc`，`--min-instances=1` |

**第 5 項是 v1 的規格債。** 腳本先寫、功能後建，這一項最後沒有建成，
而 Devpost 已誠實聲明「model-based evaluator 是 deferred 而非造假」。
**兩份文件現在一致。** 若上鏡演出雙路徑分歧，就與自己的聲明衝突。

## ❌ 腳本沒用到，一律不做

| 項目 | 為什麼砍 |
|---|---|
| 網頁 dashboard | 終端表格已足夠。做網頁是時間黑洞，而且花俏反而降低可信度 |
| S5 human approval REST | 2:25 的核准包是**顯示**，不需要真的走 REST 回寫 |
| 多輪對話介面 | 腳本裡沒有對話 |
| 即時串流輸出 | 批次跑完再顯示即可 |
| 使用者登入 / 多租戶 | 完全沒入鏡 |
| 圖表視覺化 | 3:05 的表格是純文字，不需要 chart |

> **S5 在此正式降級為「不做」，除非 WS1–WS5 全部完成且還有時間。**
> 腳本不需要它。

## ⚠️ 只需要「假到能拍」的程度

| 項目 | 最低要求 |
|---|---|
| reviewer 的 APPROVE 按鈕（1:48）| 一個 curl 或最簡 HTML 表單。**不需要真的 UI 系統** |
| 核准包版面 | 純文字對齊即可 |
| 佇列來源 | 靜態 `queue.jsonl`，不需要真的 queue service |

---

# 錄製檢查清單

## 錄之前

- [ ] Cloud Run `--min-instances=1`（前一天調，避免冷啟動）
- [ ] 跑一次完整批次，確認數字穩定（**影片裡的數字要跟 repo 裡的 evidence 一致**）
- [ ] 終端機字體放大到 16pt 以上
- [ ] 關閉所有通知
- [ ] 螢幕上不得出現 API key、`.env`、個人資訊

## 錄的時候

- [ ] **1:52 按下 APPROVE 後停 2 秒不說話**
- [ ] 3:05 的誠實聲明停留 ≥ 5 秒
- [ ] Cloud Run URL 清楚入鏡
- [ ] 不加速播放 agent 處理過程

## 錄完

- [ ] 總長 ≤ 4:00（超過會被扣分或截斷）
- [ ] 英文字幕（若旁白非英文則**必須**）
- [ ] 上傳 YouTube / Vimeo 並設為**公開**
- [ ] 用無痕視窗確認影片真的可公開存取

---

# 一句話

> **v1：腳本是規格，功能照著寫。**
> **v2：功能是事實，腳本照著改。**
>
> 兩者衝突時，改腳本，不改事實。
