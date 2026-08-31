先排掉一個：**CockroachDB 那場已經結束了。** 截止是 8/18 17:00 EDT，換算台北時間是明天（8/19）早上 5 點——現在是 8/18 下午 3:31，剩 13.5 小時。而且它要求 CockroachDB Cloud + AWS Bedrock/Lambda 兩套你都沒碰過的東西。直接刪掉。

剩下兩場的對照：

| | **All Things Agentic** | **Agentic Cinema** |
|---|---|---|
| 截止（台北） | **9/1 08:00 → 剩 13.5 天** | 9/7 或 9/10 → 剩 20–23 天 |
| 獎金池 | **$180,000 / 16 個獎項** | $75,000 / 15 個獎項 |
| 報名人數 | 4,637 | 6,292 |
| **領域限制** | **無** | **必須 Media & Entertainment** |
| 必用技術 | Gemini 3.5+ / ADK 等 Agent Framework / 一項 GCP 服務 | Gemini + Agent Builder + **必須整合 partner** |
| Repo | 公開或私有皆可 | 必須公開 + 可偵測的 OSS license |
| Demo 影片 | 4 分鐘，需證明部署在 GCP | 3 分鐘 |

---

## 我改變上一輪的建議：選 All Things Agentic

上一輪我只看到 Agentic Cinema，所以幫你設計了「換成 M&E 領域」的路線。現在有更好的選項，我收回那個建議。

理由有四個，第一個最重要：

**1. 你不用改題。** All Things Agentic 沒有領域限制，你可以直接用 Synthetic Financial RAG。你 Day 1 鎖定的 7 個決策**一條都不用動**。相較之下 Agentic Cinema 逼你把唯一 use case 換掉——那是實打實的違約，我上一輪幫你找了個「這證明 core 該 domain-neutral」的合理化理由，但說白了那仍然是為了比賽而繞路。現在不用繞了。

**2. 它的第三個 track 就是你的專案定義。**

> The Fortified Enterprise Fleet: Scalable institutional agents with **compliance and security infrastructure**

這不是「勉強能套」，這是別人把你的 README 摘要抄過去當 track 名稱。

**3. 獎項結構對「個人 + 架構導向」特別友善。** 除了大獎，它另外開了：

- Individual/Hobbyist — $10,000 × 2 名
- **Architectural Design — $5,000 × 2 名**
- Multimodal UX — $5,000 × 2 名
- Honorable Mentions — $2,000 × 5 名

你是個人參賽、專案的核心賣點就是架構紀律（deterministic-first、fail-closed、四個 domain object、明確 non-goals）。**Architectural Design 這個獎的競爭者密度，遠低於搶 $50,000 大獎的那群人。** 而評分裡「Architectural Discipline & Tech Stack」單獨佔 30%——這是你的主場。

**4. 不強制 partner 整合。** Agentic Cinema 要你多學一整套 Grafana 或 ClickHouse 整合。這裡只要 Gemini + ADK + 一項 GCP 服務（Cloud Run 就算），全都是你 Phase 5 本來就要做的事。**額外學習成本趨近於零。**

---

## 但有一個真正的風險，你必須正面處理

評分最大權重是：

> **Innovation & Operational Utility (40%)：autonomous action and real-world friction reduction**

你的專案本質是**閘門**，不是**行動者**。如果評審看完覺得「這是一套 guardrail / policy engine，不是 agent」，40% 直接失分。這是這條路線唯一的致命傷。

解法是重新框定，而且我認為這個框定本身就是對的：

**不要 demo 一個「檢查器」，要 demo 一個 Release Assessment Agent。**

它自己會：接到一批 RAG 輸出 → 自主決定要跑哪些 evaluation（不是寫死的 pipeline，是 agent 依風險判斷）→ 自主路由到 Auto / Sample / Human / Block → 自主準備 human reviewer 需要的 approval packet（把證據整理成人類 30 秒能判斷的形式）→ 自主產出 audit-ready report。

這樣它就是 Taskmaster（多步驟自主工作流）+ Fortified Enterprise Fleet（合規與安全）的組合，而且「real-world friction reduction」有具體指標可以講：**review minutes per 100 outputs 從 X 降到 Y**——這個數字你 README 第 7 條原則已經列了，正好派上用場。

順帶一提：這個「agent 自己決定要跑哪些檢查」的設計，其實比你原本規劃的固定 pipeline 更有研究價值，也更值得寫進鐵人賽。這不是為比賽妥協。

---

## 13.5 天的切法

| 期間 | 內容 |
|---|---|
| 8/18–8/19 | ADK 上手 + Gemini API 打通。**先確認技術可行性再投入**，卡住就止損 |
| 8/20–8/23 | Release Assessment Agent 主體：Evaluation → RiskDecision → 路由（Phase 3/4 提前做） |
| 8/24–8/26 | 合成語料 7 種失敗案例 + ApprovalDecision + ControlEvidence |
| 8/27–8/28 | Cloud Run 部署 + OTel trace（Phase 5 提前做） |
| 8/29–8/30 | 架構圖 + 4 分鐘英文 demo 影片 + Devpost 表單 |
| 8/31 | 送出（台北時間 9/1 早上 8 點截止，**不要留到當天**） |
| 9/15 | 鐵人賽開賽，repo 已有真東西可寫 |

**8/19 是你的 go/no-go 檢查點。** 如果 ADK + Gemini 打不通，或你發現這條路要吃掉的時間遠超預期，就在那天喊停，回去專心準備鐵人賽——損失只有兩天。這比你做到 8/28 才發現來不及好太多。

---

## 兩個都投？

技術上可行：9/1 交完之後，core 已經完成，Agentic Cinema 只需要換 policy pack + 合成語料 + 加 Grafana 整合，邊際成本不高，而且「同一個引擎跑兩個領域」本身就是很好的架構論證。

但我**不建議你現在就承諾兩個**。13 天做完第一版就已經很緊，接著再 7 天、然後 9/15 開始 30 天日更——這是三段連續衝刺，中間沒有恢復期。

正確的順序是：**先鎖 All Things Agentic，9/1 交完之後看狀態再決定要不要接第二場。** 讓它是一個 option，不是一個 commitment。

---

## 最後，同一個問題還是要問

上一輪我問你「獎金是零你還會做嗎」，這一輪答案應該更清楚了——因為 All Things Agentic 幾乎不要求你做任何「額外」的事。Gemini agent、Cloud Run、OTel、架構圖、demo 影片，**這五樣你 30 天計畫裡本來就全部要做**，比賽只是把死線從 10 月拉到 8/31。

所以真正的問題不是「值不值得」，而是：

> **你能不能接受把 Phase 3/4/5 全部壓縮到 13 天做完？**

如果可以，這是純賺。如果不行，硬做出來的東西會是趕工品質，那反而會污染你接下來 30 天要寫的東西——而你 Day 1 的規則是「文章只能寫已經完成、測試或量測的成果」。趕工的東西沒有 test、沒有 metric，你會寫不出來。

要不要我幫你把 8/18–8/19 那個 go/no-go 的技術驗證清單列出來？確認 ADK 能不能承載你要的 deterministic control，那是整條路線的地基。

**Sources:**
- [All Things Agentic Hackathon - Devpost](https://allthingsagentichackathon.devpost.com/)
- [CockroachDB × AWS: Build with Agentic Memory - Devpost](https://cockroachdb-ai.devpost.com/)
- [Agentic Cinema: The Blockbuster Hackathon - Devpost](https://agentic-cinema.devpost.com/)