# Demo 影片逐字稿 — 只有要念的部分

**配套：** 畫面與指令看 `docs/demo-storyboard.md`；素材稽核看 `docs/demo-script-v3.md`
**版本：** 2026-09-01 00:05 — 依**實測字數**重新配時（`demo-script-v3.md` 標的 S5 字數是改寫前的舊值）

---

## 念之前記住四件事

1. **超時就砍字，絕對不要加速播放。** 加速會讓「真實速度才可信」這個賣點失效
2. **兩個 82 分開講。** 「eighty-two released」是量測；時間那句只給 `240 → 43.2` 的絕對值，
   **全片不出現任何百分比**
3. **不念 AUTO / SAMPLE 的絕對值。** 那兩個數字逐跑不同，念了就跟 README 對不上
4. **S3 一定要說出 "on the live service"。** 批次裡沒有 R4 item，不講清楚就是把兩件事混為一談

**標記：** 【停 N 秒】= 完全不出聲　·　*斜體* = 重音　·　⏎ = 換氣，不是停頓

---

## 時間總表（實測 512 words，140 wpm）

| 段 | 起訖 | 長度 | 字數 | 畫面一句話 |
|---|---|---|---|---|
| S1 | 0:00–0:26 | 26s | 55 | 標題卡 → 佇列 100 筆 |
| S2 | 0:26–1:10 | 44s | 96 | 批次串流 → planner span → 無 key 對照 |
| S3 | 1:10–1:56 | 46s | 99 | live 服務 → 按下核准 → 被拒 → trajectory |
| S4 | 1:56–2:35 | 39s | 87 | ASMT-088 核准包 → 另一個行程 resolve |
| S5 | 2:35–3:24 | 49s | 109 | 指標表 → 不變量 JSON → 免責聲明 |
| S6 | 3:24–3:56 | 32s | 66 | agent card → Cloud Logging span → 結束卡 |

**純旁白 219 秒 + 明確停頓 4 秒 = 3:56**，距 4:00 上限留 4 秒。

> ⚠️ S5 是六段裡唯一沒有餘裕的。**S5 開始前先看一眼碼表**，
> 如果前面超了，砍 S5 最後那句 "and so is every one of those eighty-two releases"。

---
---

# S1 ｜ 0:00–0:26 ｜ 55 words

> 畫面：標題卡 → `wc -l` → `head | jq` → 快速捲動

Generative AI made producing answers cheap.
It did not make *approving* them cheap.
⏎
This is a queue of one hundred AI-generated answers
from a bank's internal knowledge assistant.
Today, a compliance reviewer reads every one of them
before any can be released.
⏎
That's the bottleneck. Not generation — *verification*.
⏎
Let's give the queue to the agent.

---
---

# S2 ｜ 0:26–1:10 ｜ 96 words ★ 最重要的四十四秒

> 畫面：批次串流 → planner span（ASMT-034）→ queue 那一行 → 無 key 對照 → 計數定格

The agent doesn't run a fixed pipeline.
⏎
For each item, a Gemini planner decides which checks are warranted —
here it ran citation coverage, content integrity and source freshness,
and skipped the numeric check,
because this answer makes no numeric claim.
⏎
The planner *advises*.
It never decides whether an answer may be released.
⏎
And when the planner fails — here I've pulled its API key —
it does not fall back to *fewer* checks.
It falls back to *all* of them.
Uncertainty means more scrutiny, not less.

【停 1 拍】

One hundred items, four outcomes,
and no human has read anything yet.

> ⚠️ 若 A-3 檢查顯示 planner 這次沒略過 numeric，把
> "skipped the numeric check, because this answer makes no numeric claim"
> 換成 "skipped the source-freshness check"，其餘不動。

---
---

# S3 ｜ 1:10–1:56 ｜ 99 words ★ 最強的四十六秒

> 畫面：BLOCK 那幾筆 → 切 live 服務 → 送出 R4 → 被拒 → 三行 → 停在 trajectory

Nine were blocked.
Three of them never even reached the planner —
they carry sensitive data,
so the sovereignty gate stopped them before any model saw the content.
⏎
Now the hard case, **on the live service**.
This is a prohibited operation, and I have approval authority.
Watch.

【停 2 秒 — 送出後完全不說話，讓觀眾自己反應】

The system still refused.
This policy accepts no human override —
and the attempt is now part of the record.
⏎
Note the trajectory.
It proves the block came from the R4 policy gate,
not from an earlier check that happened to fire.

【念慢】 A correct outcome reached by the wrong path is still a bug.

---
---

# S4 ｜ 1:56–2:35 ｜ 87 words

> 畫面：HUMAN_REVIEW 那幾筆 → ASMT-088 核准包 → **切到第二個終端機** resolve

The nine escalated items don't arrive as raw output.
The agent prepares a packet:
what it concluded, which policy applies,
the evidence that mattered,
and the path it took to get there.
⏎
The reviewer isn't reading an AI answer from scratch.
They're picking one of three options
against a decision the agent has already justified —

【這句要在切到第二個終端機的那一刻說】
and the resolution is written from a *separate process*,
to a store that outlives the batch.
⏎
That's the shift.
The human stays in the loop,
but only where judgment is actually required.

---
---

# S5 ｜ 2:35–3:24 ｜ 109 words ⚠️ 唯一沒有餘裕的一段

> 畫面：指標表 → highlight `240.0 → 43.2` → 不變量 JSON → 回到免責聲明

Nine escalated, nine blocked — and eighty-two released.
I've run this batch three separate times,
once with no planner API key at all,
and by assessment id those three numbers never change.
⏎
What does move is how many of the eighty-two
get sampled for audit versus auto-released outright —
that boundary depends on which checks the planner picked,
not on who gets escalated or blocked.
⏎
The time figure next to it is an estimate
on a two-point-four minute baseline
with no timed pilot behind it —
and it says so on screen.
⏎
The point isn't the number.
It's that the number is auditable,

【超時就砍下面這半句】
and so is every one of those eighty-two releases.

> ★ 免責聲明要留在畫面上累計 ≥ 5 秒。
> ⚠️ 不出現百分比，時間只講 `240 → 43.2`。

---
---

# S6 ｜ 3:24–3:56 ｜ 66 words

> 畫面：agent card（網址列入鏡）→ Cloud Logging 撈 span → 六行屬性 → 結束卡

All of this runs on Google Cloud Run,
built with Gemini and the Agent Development Kit.
⏎
Every policy decision emits an OpenTelemetry guardrail span.
Here it is in Cloud Logging, from the request you just saw —
the policy, the decision,
and which plugin in the chain made it.
⏎
An auditor can ask not just *what* the agent decided,
but *which control* decided it.
⏎
【念慢】 Evidence, not assurances.

【停 2 秒再結束】

---
---

## 全片的三句金句（念的時候慢下來）

1. **"Uncertainty means more scrutiny, not less."**（S2）
2. **"A correct outcome reached by the wrong path is still a bug."**（S3）
3. **"Evidence, not assurances."**（S6）
