# 《Observability ≠ Evaluation ≠ Assurance：看得到 AI，不代表敢讓它上線》

### 從 AI 可觀測到 AI 可核准：30 天打造 Risk-Adaptive AI Assurance Pipeline — Day 2

---

昨天我把問題和範圍鎖住了。

今天要處理的是一個更基礎、但經常被跳過的問題：

**我們到底在談哪一層？**

因為在「AI 上線前要做什麼」這件事上，市面上至少有三種完全不同的東西，經常被放在同一個句子裡討論：

```text
Observability
Evaluation
Assurance
```

如果這三個詞混著用，會發生一件很具體的事：

> 團隊買了一套工具，接上 dashboard，看到 latency、token、trace、retrieval，然後主管問「所以這個可以上線了嗎」——
> 沒有人答得出來。

因為**那套工具從一開始就不是為了回答這個問題設計的。**

---

## 這不是我一個人的觀察

在開始拆解之前，我想先說明為什麼今天要花一整篇來處理定義問題。

今年的 iThome AI Enterprise Summit 有兩場議程，剛好落在這個題目的上下游：一場來自 Microsoft，主題是企業負責任 AI 與 Agent 治理；一場來自國泰金控，主題是企業級 Agentic AI 的可觀測性架構。

我不會在這裡轉述兩場簡報的內容——那是講者的成果，也不是我能代為發表的。但**這兩場議程同時出現在同一個議程表上，本身就是一個訊號**：

> 在 2026 年，「Agent 上線前要看什麼」已經是企業級的實務問題，不是研究議題。

而且如果你把視角再拉遠一點，會看到一個更有意思的現象。

我最近陸續看到幾組完全不同背景的人——雲端廠商的工程師、金融業的架構師、獨立開發者——各自用不同的話講同一件事。用我自己的話重述，大概是這四句：

- HTTP 200，不代表它答對了
- 傳統系統壞掉會噴 500，Agent 壞掉會回 200
- 用錯誤的推理得到正確答案，仍然是 bug
- 最終結果正確，不代表 Agent 行為正確

不同的立場、不同的產業、不同的技術棧，收斂到同一個判斷。

**這對我來說有兩個意義。**

第一個是好消息：我昨天鎖定的題目，不是我自己想像出來的需求。

第二個是壞消息，而且更重要：

> **「指出這個問題」已經沒有差異化了。**

大家都看到了。所以接下來 29 天，我不打算再花篇幅論證「為什麼 assurance 重要」——那在 2026 年是常識。我要證明的是**它能不能被做出來**。

---

## 第一層：Observability —— What happened?

先講最成熟的一層。

可觀測性回答的是「剛才發生了什麼」。對一般應用來說，這是延遲、錯誤率、吞吐量。對 AI 應用來說，這一層已經延伸到：

```text
model
token count
latency
trace / span
retrieval result
tool call
error
```

這一層在 2026 年已經有標準了。OpenTelemetry 提供傳輸與資料格式，而 **OpenInference** 蓋在它之上，提供 AI 專用的語義慣例——把 span 分成十種 kind（`LLM`、`TOOL`、`AGENT`、`CHAIN`、`RETRIEVER`、`GUARDRAIL`、`EVALUATOR` 等），並且標準化 `llm.input_messages`、`llm.token_count.prompt` 這類屬性命名空間。

順帶一提，`GUARDRAIL` 和 `EVALUATOR` 這兩個 span kind 的存在本身就很有意思——它代表**「這一段執行是在做把關 / 評估」已經被認為值得在遙測層被標示出來**，而不只是另一個函式呼叫。這件事等一下會回來。

這件事的價值比它聽起來大。

因為在傳統軟體裡，**程式碼就是文件**——你讀原始碼，就知道系統會做什麼。

但 Agent 不是。Agent 的控制流是**執行期才決定**的。同樣的輸入，可能走出不同的路徑。你讀 `agent.py` 只會看到「這裡有五個工具、一段 instruction」，你讀不出它昨天下午三點到底做了什麼。

所以在 Agent 系統裡：

> **Trace 才是文件。**

這句話等一下會變得很重要。

---

## 第二層：Evaluation —— How good / safe was it?

第二層回答的是品質與安全。

```text
groundedness
citation coverage
task completion
hallucination
policy violation
regression
```

這一層也在快速成熟。而且很值得注意的是，Evaluation 本身正在分裂成兩個子問題：

**Outcome Evaluation（結果評估）**
評的是最終產出——答案對不對、有沒有引用、格式合不合規。用 regex、JSON schema、exact match，或 LLM-as-a-Judge 打分。

**Trajectory Evaluation（軌跡評估）**
評的是**它是怎麼得到這個答案的**——選對工具了嗎？有沒有繞路？有沒有跳過該做的檢查？

第二個之所以存在，是因為一件很反直覺的事：

> **結果正確，不代表行為正確。**

我在昨天的文章裡提過我的專案有一個測試案例。今天可以把它講清楚一點。

假設有一個高風險操作被系統擋下來了。最終狀態是 `BLOCKED`。

但這個 `BLOCKED` 可能來自兩條完全不同的路徑：

```text
路徑 A：
  RiskEngine 判定為 R4 → HardPolicyCheck → BLOCKED

路徑 B：
  LLM 自己決定不呼叫那個工具 → 沒有動作 → BLOCKED
```

**最終結果一模一樣。任何只斷言 `result == "BLOCKED"` 的測試，兩條路徑都會 PASS。**

但這兩件事的性質完全不同：

- 路徑 A 是**保證**
- 路徑 B 是**運氣**

而運氣是不能拿去稽核的。你不能在半年後跟稽核人員說「那次它剛好沒做」。

所以 Trajectory Evaluation 不是錦上添花，它是在回答「這個結果是不是可重現的」。

---

## 第三層：Assurance —— Can we approve it, and why?

現在來到我這 30 天真正要做的東西。

前兩層都很重要，而且都在快速成熟。但它們有一個共同的終點：

**它們產生的是資訊，不是決定。**

Observability 告訴你發生了什麼。
Evaluation 告訴你它做得好不好。

然後呢？

真正要上線的時候，組織需要的是一個**決定**：

```text
PASS
REVIEW_REQUIRED
BLOCK
```

而且這個決定不能只有一個分數。它必須能回答：

> **根據什麼 evidence？**
> **依據哪一條 policy？**
> **誰批准的？**
> **如果之後出事，證據在哪？**

這就是我暫時把它叫做 **Assurance** 的原因。

三層的關係可以這樣看：

```text
Observability
    ↓
What happened?
    ↓
Evaluation
    ↓
How good / safe was it?
    ↓
Assurance
    ↓
Can we approve it, and why?
```

---

## 為什麼這個區分不只是文字遊戲

因為**三層的失敗模式完全不同**。

| | 失敗長什麼樣 | 誰會先發現 |
|---|---|---|
| Observability 失敗 | 看不見。出事了不知道 | 事後回溯的工程師 |
| Evaluation 失敗 | 看得見但沒判斷。分數漂亮，實際上錯 | 使用者，通常是幾週後 |
| **Assurance 失敗** | **有判斷但不可辯護。出事時拿不出證據** | **稽核人員、法遵、法務** |

第三種最貴，而且**最晚被發現**。

一個團隊可以觀測完備、評估完備，然後在被問到「這次放行的依據是什麼」的時候，只能拿出一堆 log 和一個 Slack 對話截圖。

那不是證據。那是回憶。

---

## 第一版架構圖

把三層放進實際的資料流，是這個樣子：

```text
                    Source / Input
                          │
                          ▼
                 ┌─────────────────┐
                 │ Evidence        │  ← 保存原始證據
                 │ Ingestion       │     在任何機率性處理之前
                 └────────┬────────┘
                          │
                          ▼
                    T0 Evidence
                          │
                          ▼
                 ┌─────────────────┐
                 │ Source          │  ← Fail Closed
                 │ Governance      │     未登記 = UNKNOWN = 禁止外送
                 └────────┬────────┘
                          │
                ┌─────────┴─────────┐
                │                   │
              ALLOW               BLOCK
                │
                ▼
          ┌──────────┐
          │    AI    │  ─────────────┐
          │Processing│               │  Observability
          └─────┬────┘               │  (OTel + OpenInference)
                │                    │  ← What happened?
                ▼                    │
          ┌──────────┐               │
          │Evaluation│ ──────────────┤  Evaluation
          │          │               │  ← How good / safe?
          │ Outcome  │               │
          │Trajectory│               │
          └─────┬────┘               │
                │                    │
                ▼                    │
          ┌──────────┐               │
          │  Policy  │               │
          │  Engine  │               │  ← 確定性，不交給 LLM
          └─────┬────┘               │
                │                    │
                ▼                    │
          ┌──────────┐               │
          │   Risk   │               │  Assurance
          │  Router  │               │  ← Can we approve it?
          └─────┬────┘               │
                │                    │
    ┌───────┬───┴────┬─────────┐     │
    ▼       ▼        ▼         ▼     │
   R0/R1   R2       R3        R4     │
   Auto  Sample   Human     Block    │
                    │               │
                    ▼               │
            ApprovalDecision        │
                    │               │
                    ▼               │
            ControlEvidence  ◄──────┘
                    │           trajectory 從 span tree 抽取
                    ▼
              Audit / Report
```

有三個地方我想特別說明。

**第一，Observability 貫穿全程，但它不做決定。**
右側那條虛線是 trace，它從頭到尾記錄，但它不決定任何事。它是決定的**輸入**，不是決定本身。

**第二，Policy Engine 不是 LLM。**
這是我昨天鎖定的原則之一：能確定性檢查的，不要交給機率性系統做最終決定。Risk Router 依據的是政策引擎算出來的等級，不是模型的判斷。

**第三，ControlEvidence 吃 trajectory。**
還記得前面那句「Trace 才是文件」嗎？這裡就是它的用處。ControlEvidence 不只記錄「結論是什麼」，還要記錄「**走過哪條路徑得到這個結論**」。

因為要證明的不是「答案對」，是「答案是透過被核准的控制路徑產生的」。

而這也是前面提到 `GUARDRAIL` 與 `EVALUATOR` 那兩個 span kind 會回來的地方——如果把關動作在遙測層就被標示出來，那麼「這條路徑有沒有經過該有的把關」就變成一個**可以被機器查詢的問題**，而不是要靠人去讀 log 推敲。

---

## 一個我還沒解決的問題

在準備這篇的時候，我看到一位開發者在做 Agent workflow 的實驗，他提出一個我覺得很值得記錄的疑問：

> 如果把執行軌跡約束得太嚴格，會不會反過來消滅 Agent 原本應有的自主性？

我目前的立場是：**這是一個假兩難，解法是約束 invariant，而不是約束 path。**

不要斷言「實際路徑必須等於黃金路徑」——完整的路徑覆蓋在組合上就是爆炸的，本來就做不到。要斷言的是性質：

| 類型 | 範例 |
|---|---|
| **禁止轉移** | 外部模型呼叫的前驅，不得是未解析的 UNKNOWN 來源 |
| **必要前驅** | 任何核准動作之前，必須經過 hard policy 檢查 |
| **副作用基數** | 單次評估中，外送次數不得超過政策允許值 |
| **強制檢查點** | R3 路徑必須包含 ApprovalDecision，R4 必須包含 HardBlock |

自主性活在這些 invariant 之間的空隙裡。

這和型別系統不會消滅程式設計自由是同一個道理：**它約束的是非法，不是規定合法。**

但我必須誠實說：**這是我今天的假設，不是我已經驗證過的結論。** 它會在後面幾天被實作檢驗，如果做出來發現這個界線抓錯了，我會回來修正這一段。

---

## 今天的邊界

最後，照昨天訂的規則，說清楚今天做了什麼、沒做什麼。

**今天完成的：**

- 三層邊界的定義固定下來
- 第一版架構圖
- 確認 Observability 這一層採用既有標準（OpenTelemetry + OpenInference），不自創 span schema
- 確認 ControlEvidence 必須包含 trajectory 欄位

**今天沒有做的：**

- 沒有寫 Evaluation 的實作
- 沒有寫 Risk Router
- 沒有做任何 trajectory 斷言
- 沒有驗證 OpenInference 的 auto-instrumentor 真的能在我的環境跑起來

**這些都還是 planned，不是 done。**

我特別想強調這一點，因為畫架構圖是這類專案最容易自我欺騙的環節——圖畫得越漂亮，越容易產生「已經做完了」的錯覺。

架構圖只是假設。**它要等到有測試通過，才變成事實。**

---

明天 Day 3，我會開始碰第一段真正的實作：確認我選的 Agent 框架能不能承載這裡畫的 deterministic control——特別是**「硬性政策不能被人工核准繞過」**這一條，能不能在框架層真的做到，而不只是在我的圖上做到。

如果做不到，我會把失敗寫出來。

---

*本系列所有文章對應的程式碼、測試與失敗紀錄，都會同步在 GitHub。文章是工程結果的紀錄，不是 Roadmap 的文學版。*
