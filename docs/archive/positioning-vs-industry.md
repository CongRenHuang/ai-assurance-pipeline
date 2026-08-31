# 三方定位比較：治理平台 / 觀測體系 / 決策層

**建立日期：** 2026-08-18
**用途：** 專案定位的競品與同溫層分析，作為 Day 2 文章與 README 定位段落的依據
**引用邊界：** 本文件僅記錄兩場公開研討會議程層次的「主題與關注點」，以及可公開查證的技術標準（OpenTelemetry、OpenInference、OWASP ASI、ADK 官方文件）。**不重製任何非公開簡報內容、不引用投影片文字、不代述講者未公開發表的主張。** 所有具體技術陳述均以官方文件為準並附連結。

---

## 一、為什麼要做這份比較

專案的 North Star 是：

> **How do we turn AI evidence into defensible decisions?**

在投入 13 天衝刺之前，必須先確認兩件事：

1. **這個問題是不是真的存在？** —— 或者只是我自己想像出來的需求
2. **如果存在，別人已經做到哪裡？** —— 我的差異化到底在哪一層

2026 年 iThome AI Enterprise Summit 有兩場議程正好落在這個題目的上下游：一場來自 Microsoft，講企業負責任 AI 與 Agent 治理；一場來自國泰金控，講企業級 Agentic AI 的可觀測性架構。兩場的存在本身就是訊號。

---

## 二、定位光譜

三者解的不是同一個問題，而是**同一條光譜上的不同段落**。

```text
        治理原則              可觀測性              決策與放行
           │                     │                      │
    ┌──────┴──────┐      ┌──────┴──────┐       ┌───────┴───────┐
    │  平台與標準  │      │  訊號與追蹤  │       │  證據與核准    │
    │             │      │              │       │               │
    │ 邊界 / 檢查點│      │ Trace / Eval │       │ Evidence      │
    │ / 稽核       │      │ / Golden     │       │ → Risk        │
    │             │      │   Signals    │       │ → Approval    │
    │             │      │              │       │ → Control     │
    │             │      │              │       │   Evidence    │
    └─────────────┘      └──────────────┘       └───────────────┘
       大型雲廠商            企業架構團隊            本專案
```

| 面向 | 治理平台路線 | 可觀測性路線 | 本專案 |
|---|---|---|---|
| **核心提問** | 企業什麼時候敢把權限交給 Agent？ | Agent 靜默失敗了，我怎麼看見？ | 看見之後，誰決定放行、依據什麼？ |
| **主要交付** | 平台能力 + 法遵框架對齊 | 參考架構 + 追蹤與評估管線 | **可執行的決策管線** |
| **抽象層次** | 組織與制度 | 系統與訊號 | **單次決策** |
| **成功定義** | 企業敢採用 | 問題看得見、可歸因 | 決策可被批准、拒絕、追溯 |
| **典型產物** | SDK、政策引擎、合規對照 | Trace schema、Dashboard、Eval 集 | RiskDecision / ApprovalDecision / ControlEvidence |
| **角色比喻** | 賣鏟子的 | 挖礦的 | 做礦場驗收流程的 |

---

## 三、關鍵發現一：問題本身已是共識

在準備這份比較的過程中，注意到一個現象：**多個背景完全不同的來源——雲廠商、企業架構團隊、獨立開發者——各自獨立收斂到同一個判斷。**

以下是這個共識的幾種常見表述形式（產業普遍觀察，非特定來源引述）：

| 切入角度 | 表述形式 |
|---|---|
| 可觀測性方向 | 傳統系統壞掉噴 500，Agent 壞掉回 200——失敗是靜默的 |
| 評估方向 | 結果正確不代表推理正確；用錯的路徑得到對的答案仍是 bug |
| Workflow 可靠性方向 | 最終結果正確，不代表 Agent 行為正確 |
| **本專案的表述** | **人按了核准，系統仍然拒絕**（S6 規劃驗證項） |

### 這代表什麼

**好消息：** 選題不需要再懷疑。「AI 產出的驗證成本高於生成成本」在 2026 年是產業共識，不是個人臆測。North Star 站得住。

**壞消息（更重要）：** **「指出這個問題」已經沒有差異化了。** 大家都看到了。

### 對專案的直接影響

> **不要再花篇幅論證「為什麼 assurance 重要」。那是 2026 年的常識。**
>
> 差異化必須落在「**做出可執行的那一層**」——working code、可重現的測試、失敗案例、可量測的指標。

這條原則直接適用於 30 天文章的配置：問題論述最多佔 Day 1–2，之後每一篇都必須有工程 artifact 支撐。

---

## 四、關鍵發現二：兩條既有路線共同的斷點

治理路線與觀測路線都很成熟，但兩者都停在同一個地方：

**治理路線**能定義行動邊界與權限範圍，並在 Agent 生命週期中埋入可喊停的檢查點。

**觀測路線**能把每一次模型呼叫、工具呼叫、檢索結果變成可查詢的 trace，並區分「結果評估」與「軌跡評估」。

**但兩者都沒有回答：**

1. 呈核之後，**那筆核准證據長什麼形狀**？
2. 半年後稽核時，**要拿什麼去證明「當時的放行是合規的」**？
3. 當人工核准與硬性政策衝突時，**誰贏**？
4. 「這個答案走過了被核准的控制路徑」這件事，**要怎麼被機器驗證**？

這四個問題就是本專案的位置。

```text
    治理平台              可觀測性                【 本專案 】
       │                     │                        │
   定義邊界              產生訊號                 產生決策與證據
       │                     │                        │
   「不准做 X」          「它做了 Y」          「Y 可以被批准，因為 Z」
                                                      │
                                              ┌───────┴───────┐
                                              │ ControlEvidence│
                                              │ requirement    │
                                              │  → control     │
                                              │  → test        │
                                              │  → evidence    │
                                              └────────────────┘
```

---

## 五、可借鏡且不會發散的四件事

判準：**替換既有工作項，而非新增工作項。**

### ① 採用 OpenInference 作為 span 語義標準

**理由：** 專案本來就要做 OTel decision trace，本來就要決定 span 怎麼命名。用既有標準與自創標準的工作量相同，但前者讓 trajectory 可被任何標準工具讀取。

**以下為官方文件與 PyPI 頁面的宣稱，尚未在本專案實測**（見第九節待驗證清單）：

- OpenInference 建構於 OpenTelemetry 之上，為 agentic 應用提供 AI 專用 semantic convention
- Span kind 共十種：`LLM` / `TOOL` / `AGENT` / `CHAIN` / `RETRIEVER` / `RERANKER` / `EMBEDDING` / `GUARDRAIL` / `EVALUATOR` / `PROMPT`
- 屬性命名空間標準化：`llm.input_messages`、`llm.output_messages`、`llm.token_count.prompt` 等
- `openinference-instrumentation-google-adk`（v0.1.20，2026-08-12）提供 ADK auto-instrumentor
- 可直接接一般 OTLP exporter，不強制綁定任何商業平台

> **意外紅利：** 十種 span kind 裡有 **`GUARDRAIL`** 與 **`EVALUATOR`**，正好對應本專案的 policy check 與 evaluation 概念。等於免費取得語義對齊——稽核工具讀 trace 時能直接辨識這些 span 的性質，不需要自訂慣例。

**專案僅需新增四個自訂屬性：**

```text
assurance.risk_tier          R0–R4
assurance.policy_id          觸發的政策編號
assurance.decision           AUTO / SAMPLE / HUMAN_REVIEW / BLOCK
assurance.override_rejected  人工核准被 hard policy 駁回時為 true
```

**額外紅利：** trajectory 可直接從 span tree 的父子關係抽取，省去手動記錄。

### ② 「Trace 就是文件」作為 ControlEvidence 的理由

傳統軟體中，程式碼即文件——讀原始碼就知道系統會做什麼。但 Agent 的控制流是**執行期才決定**的，讀原始碼看不出它實際做了什麼。因此在 Agent 系統中，**trace 才是文件**。

這是 `ControlEvidence` 必須包含 trajectory 欄位的最簡潔理由，可直接用於 README 與文章。

### ③ 三層測試分層命名

專案已有三層測試，只是缺乏命名。採用業界通行分層讓結構一眼可讀：

| 層級 | 內容 | 專案對應 |
|---|---|---|
| Tier 1 · Unit | 純函式驗證、框架內建 local eval | deterministic evaluator（citation 檢查、hash 比對、TTL 驗證） |
| Tier 2 · Integration | **Trajectory-level**、LLM-as-a-Judge | trajectory assertion + model-based evaluator |
| Tier 3 · E2E | HITL、人工標註 | human approval 流程、hard policy 覆寫測試 |

**這是零成本的加分**——不新增工作，只是給既有結構一個可溝通的名字。

### ④ 「原則 → 需求 → 證據」的逐層展開結構

成熟組織處理負責任 AI 的共同做法，是把抽象原則逐層拆解為可驗收的需求與具體證據，而非停在宣言層次。這個模式在 NIST AI RMF 的 Govern → Map → Measure → Manage 中也看得到同樣的精神。

`ControlEvidence` 採用同構的形狀（此展開結構為本專案自訂）：

```text
requirement  →  control  →  test  →  evidence
```

**採用其結構邏輯，不模仿其組織規模。**

---

## 六、必須過濾的雜訊

判準：**這一項是廠商的必需品，還是我的必需品？**

| 誘因 | 為什麼要跳過 | 折衷做法 |
|---|---|---|
| **OWASP ASI Top 10 全覆蓋** | 平台廠商必須宣稱 10/10 因為它在賣治理平台。13 天做 10 項每項都淺；做 2 項做到能演示攻擊被擋才有說服力 | **只做 ASI01（Agent Goal Hijack）與 ASI03（Identity & Privilege Abuse）**——S1 / S6 的**規劃**驗證項涵蓋這兩項，待 spike 完成後才寫入 README。⚠️「Excessive Agency」是舊版 LLM Top 10 的 LLM08，**不是** ASI09（ASI09 為 Human-Agent Trust Exploitation），編號務必查證 |
| **法遵框架對照表**（EU AI Act / NIST RMF / SOC 2 / ISO 42001） | 法遵對齊是**組織行為**，不是個人專案能宣稱的。README 的 non-goals 已明列「不提供法遵認證」 | 一句話說明 risk tier「參考 NIST AI RMF 的風險分級精神」，然後停。**不做對照表**——做了就是往 GRC 平台漂移 |
| **AI Gateway / Proxy 層** | 企業級架構需要（Auth / RateLimit / Caching），13 天不需要 | egress gate 放在框架的 plugin 層即可。加 gateway 只增加部署複雜度與 demo 解說負擔 |
| **Agent 自動最佳化 / ROI 儀表板** | 平台功能，不可能也不需要重做 | review economics 指標（review minutes per 100 outputs）已覆蓋 ROI 論述中有用的部分 |
| **Golden Dataset + Experiments 持續營運閉環** | 正確的長期架構，但那是**持續營運**的迴圈，不是 13 天能建立的資產 | trace viewer 可本機起一個來看（省自製 UI 時間），但**只用它看，不用它管** |

---

## 七、一句話定位（可直接用於簡報與 README）

> **治理路線給你權限邊界，觀測路線給你行為訊號，但兩者都停在「看得到、擋得住」。**
>
> **本專案回答下一個問題：看到了之後，誰批准、依據什麼、證據留在哪。**

---

## 八、對 30 天計畫的實際影響

| 項目 | 變更 | 預期性質（未實測） |
|---|---|---|
| S7 Decision Trace | 改用 OpenInference auto-instrumentor + 四個 `assurance.*` 自訂屬性 | **替換**（預估工作量不變；若 instrumentor 不相容則退回手動 span，+1 小時） |
| S9 Trajectory | 從 OpenInference span tree 抽取，不手動 append | **簡化**（預估省 1 小時；若抽取粒度不足則 +1 小時） |
| README 測試策略 | 改用三層分層命名 | **重新命名**（零成本） |
| README 安全宣稱 | 明確標注僅覆蓋 ASI01 / ASI03，且待 spike 完成後才寫入 | **收斂**（降低過度宣稱風險） |
| 文章配置 | 問題論述壓縮至 Day 1–2，之後每篇必須有 artifact | **紀律強化** |

**未新增任何模組、未擴大 v0.1 範圍、未變更 Day 1 鎖定的七項決策。**

---

## 九、待驗證與開放問題

- [ ] **★ graph workflow 是否與 OpenInference auto-instrumentor 相容**（若不相容，S7 + S9 同時受影響——唯一的單點雙殺風險，S0 就要確認）
- [ ] OpenInference auto-instrumentor 與實際安裝的 ADK 版本是否相容（S7 驗證）
- [ ] `GUARDRAIL` / `EVALUATOR` span kind 能否在 auto-instrumented 環境中手動指定
- [ ] `assurance.*` 自訂屬性能否穩定寫入 auto-instrumented span（S7 驗證）
- [ ] trajectory 從 span tree 抽取的粒度是否足以支撐 invariant 斷言（S9 驗證）
- [ ] 開放問題：軌跡約束的鬆緊界線在哪？目前的立場是「**約束 invariant，不約束 path**」——禁止轉移、必要前驅、副作用基數、強制檢查點。完整 path coverage 在組合上不可行，因此本來就只能斷言性質而非路徑

---

## 參考來源

技術標準與官方文件：

- [OpenTelemetry](https://opentelemetry.io/)
- [openinference-instrumentation-google-adk — PyPI](https://pypi.org/project/openinference-instrumentation-google-adk/)
- [ADK — Phoenix / OpenInference 整合](https://adk.dev/integrations/phoenix/)
- [ADK — Observability](https://adk.dev/observability/)
- [ADK 2.0 — Graph-based agent workflows](https://adk.dev/graphs/)
- [OWASP GenAI Security Project](https://genai.owasp.org/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

研討會議程（僅記錄主題層次）：

- iThome AI Enterprise Summit 2026 — 企業負責任 AI 與 Agent 治理場次（Microsoft）
- iThome AI Enterprise Summit 2026 — 企業級 Agentic AI 可觀測性架構場次（國泰金控）
