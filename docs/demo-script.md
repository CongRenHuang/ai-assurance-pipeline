# 4 分鐘 Demo 影片逐字腳本

**專案：** Release Assessment Agent
**用途：** All Things Agentic 提交（4 分鐘上限、需含 GCP 部署證明、英文或英文字幕）
**版本：** v1 — 2026-08-21
**規則：** 這份腳本是**規格**。WS1–WS4 只做腳本裡出現的東西；沒出現的一律不做。

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
- 1:00 停在某一筆，highlight 該筆的 evaluator 選擇：
  ```
  ASMT-042  selected: [citation_coverage, source_governance]
            skipped:  [content_integrity]  reason: no hash claim
  ```
- 1:15 畫面切到「兩條路徑」示意：deterministic vs model-based，兩者**不一致**
- 1:25 該筆被自動升級為 R3
- 1:30 回到總覽，四類計數定格

**旁白**

> The agent doesn't run a fixed pipeline.
> For each item it decides which checks are warranted — here it selected citation coverage and source governance, and skipped content integrity because this answer makes no hash-verifiable claim.
>
> Every item is checked twice, independently: a deterministic evaluator and a model-based one.
> When the two agree, confidence is high.
> When they disagree — like this one — the agent escalates it to a human. It does not guess.
>
> One hundred items. Four outcomes. No human has read anything yet.

**製作備註**
- **1:15 那個「兩條路徑分歧」是本片第二強的畫面**，一定要看得清楚
- 「It does not guess」後面停 1 拍
- 計數器最終定格：`AUTO 87 · SAMPLE 9 · HUMAN 2 · BLOCK 2`

---

## 【1:35–2:20】硬性政策不可覆寫 ｜ 96 words ★ 本片最強的 45 秒

**畫面**
- 1:35 zoom 到 BLOCK 那 2 筆其中一筆：`ASMT-088  R4 PROHIBITED`
- 1:42 **切到 reviewer 視角**，畫面上有一個 APPROVE 按鈕
- 1:48 游標移過去，**按下 APPROVE**（動作要慢，讓觀眾看清楚）
- 1:52 系統回應：紅底 `BLOCKED — OVERRIDE_REJECTED`
- 2:00 切到 ControlEvidence JSON，highlight 三行：
  ```
  "result": "OVERRIDE_REJECTED"
  "policy_id": "FIN-AI-004"
  "trajectory": ["hard_policy_gate", "hard_block"]
  ```
- 2:12 停在 trajectory 那一行

**旁白**

> These two were blocked outright.
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
- 2:20 切到 HUMAN 那 2 筆
- 2:25 顯示核准包（純文字，終端機或簡單卡片）：
  ```
  ASSESSMENT ASMT-042              RISK R3 — needs your judgment
  ──────────────────────────────────────────────────────────
  Recommendation   REVIEW   (agent will not auto-release)
  Policy           FIN-AI-001  unregistered source
  Key evidence     citation coverage 0.62  (threshold 0.80)
                   deterministic and model evaluators disagree
  Trajectory       evidence → evaluate → risk_router[R3] → human
  Your decision    Register this source, or reject the release.
  ──────────────────────────────────────────────────────────
  ```
- 2:50 reviewer 快速掃過、做出決定
- 3:00 該筆狀態變更，evidence 更新

**旁白**

> The two escalated items don't arrive as raw output.
> The agent prepares a packet: what it concluded, which policy applies, the evidence that mattered, and the path it took to get there.
>
> The reviewer isn't reading an AI answer from scratch.
> They're confirming a decision the agent has already justified — in about thirty seconds.
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
  100 assessments
  ─────────────────────────────────────────
  Auto-approved       87    each with ControlEvidence
  Sampled              9
  Human review         2
  Hard-blocked         2    incl. 1 OVERRIDE_REJECTED
  ─────────────────────────────────────────
  Review minutes      240 → 18      (estimated baseline)
  Compute cost        $X  → $Y      (risk-tiered evaluation)
  ─────────────────────────────────────────
  Synthetic corpus. Baseline is an estimate, not measured.
  ```
- 3:25 highlight `240 → 18`

**旁白**

> Here's the whole batch.
> Eighty-seven auto-approved, each with audit evidence. Nine sampled. Two escalated. Two blocked.
>
> Estimated review time drops from about four hours to eighteen minutes, and compute cost falls because low-risk items don't run expensive checks.
>
> This is a synthetic corpus and the baseline is an estimate — both are stated on screen.
> The point isn't the exact number. It's that the number exists at all, and every one of those eighty-seven approvals can be audited.

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

| # | 功能 | 出現時間 | WS | 沒有會怎樣 |
|---|---|---|---|---|
| 1 | **批次 runner**（100 筆佇列）| 0:08–1:35 | WS1 | **整支影片沒有開場**，退回單筆 = middleware 敘事 |
| 2 | **四類分流計數** | 1:30, 3:05 | WS1 | 沒有「agent 做了很多事」的證據 |
| 3 | **每筆 ControlEvidence** | 2:00, 3:10 | WS1 | 87 筆自動核准變成無根據 |
| 4 | **evaluator 選擇 + 理由** | 1:00 | WS2 | **失去 autonomous 的唯一直接畫面** |
| 5 | **雙路徑交叉比對 + 分歧升級** | 1:15 | WS2 | 失去第二強畫面；升級變成無理由 |
| 6 | **R4 + 人工核准被拒** | 1:35–2:20 | ✅ 已完成 | 失去最強 45 秒 |
| 7 | **trajectory 在 evidence 裡** | 2:00 | ✅ 已完成 | 「正確結果錯誤原因」講不出來 |
| 8 | **核准包產生器** | 2:25 | WS4 | 人的角色回到「被拒絕」，摩擦力故事斷掉 |
| 9 | **指標表格**（含誠實聲明）| 3:05 | WS3 | **40% 沒有量化證據** |
| 10 | **Cloud Run 可存取 + trace viewer** | 3:35 | ✅ 已完成 | 沒有部署證明，違反提交要求 |

**6、7、10 已經完成。實際要新建的只有 1–5、8、9 共七項。**

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

> **腳本是規格。** 這十項功能之外的任何東西，在 9/1 之前都不要寫。
