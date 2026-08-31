All Things Agentic Hackathon Summary Notes

This global hackathon offers a $180,000 prize pool to build autonomous, multi-step AI agents leveraging Gemini 3.5 and Google Cloud ($150 GCP credits provided upon registration).

Challenge Tracks (Choose One)

* Track 1: The Taskmaster
  
  * Core Focus: Action-oriented automation rather than standard chat interfaces.

  * Scope: Solve complex, multi-step chores across work or personal workflows by taking autonomous action and routing data across external systems.

* Track 2: The Collaborative Partner
  
  * Core Focus: Adaptive guidance and collaborative decision-making.

  * Scope: Guide users step-by-step, ask clarifying questions, and continuously adapt to user feedback and thinking patterns.

* Track 3: The Fortified Enterprise Fleet
  
  * Core Focus: Scalable, secure, and compliant multi-agent networks integrated with production systems.

  * Architecture Components:

    * Discovery & Lifecycle: Agent Registry for publishing, versioning, and discovery.

    * Core Execution & State: Agent Runtime (long-running background execution) and Memory Bank (persistent cross-session context).

    * Security & Governance: Agent Identity (zero-trust access), Agent Gateway (unified routing/policy), and Model Armor (guardrails against prompt injection, tool poisoning, and PII leaks).

    * Telemetry: Agent Observability (OpenTelemetry-compliant audit logs and reasoning traces).

Mandatory Technical Requirements

1. AI Model: Gemini 3.5 or newer accessed via Gemini API or Vertex AI.
  
2. Agent Framework: At least one Google framework (Google ADK, GenAI SDK, Antigravity SDK, or GenKit).
  
3. Cloud Infrastructure: At least one Google Cloud service (e.g., Cloud Run, Cloud SQL, Firestore, GKE, Pub/Sub).
  
Judging Criteria

```
| Criteria                              | Weight | Focus Areas                                                                                             |
| ------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------- |
| Innovation & Operational Utility      | 40%    | Real-world friction removed autonomously; emphasizes functional execution over conversation.            |
| Architectural Discipline & Tech Stack | 30%    | System decoupling, state/memory persistence, credential security, and fault tolerance.                  |
| Demo & Production Readiness           | 30%    | Live demo quality, architecture clarity, reproducible setup guide, and visible proof of GCP deployment. |
```

Submission Checklist

* [ ] Category/Track Selection
  
* [ ] Project Description: Features, tech stack, data sources, and findings/learnings.
  
* [ ] Architecture Diagram: Visual mapping of Gemini, backend services, databases, and frontend interfaces.
  
* [ ] Code Repository (GitHub / GitLab / Bitbucket): Must include a reproducible setup guide (README.md). If private, grant access to <testing@devpost.com> and <cloudhackathons@google.com>.
  
* [ ] ~4-Minute Demo Video: Problem overview, value proposition, live end-to-end demo, and visible proof of running on Google Cloud (e.g., Cloud Run console, Vertex AI logs, .run domain).
  
* [ ] Hosted Project Link (Optional): Public web UI, extension, or mobile build (strongly encouraged).
  
Bonus Points

* Public Content Creation: Publish an article, podcast, or video (Medium, dev.to, YouTube) detailing how the project was built, stating it was made for this hackathon.
  
* Social Promotion: Share on X, LinkedIn, Instagram, or Facebook using #AllThingsAgenticHackathon.
  
* Google AI Model Integration: Integrate additional Google models such as Gemma, Veo, or Lyria.
Prize Distribution

```
| Prize Category                    | Winners | Cash (USD) | GCP Credits (USD) | Additional Perks                               |
| --------------------------------- | ------- | ---------- | ----------------- | ---------------------------------------------- |
| Grand Prize                       | 1       | $50,000    | $5,000            | Virtual Coffee with Google Team + Social Promo |
| Track Winners (3 Tracks)          | 1 each  | $20,000    | $2,000            | Virtual Coffee with Google Team + Social Promo |
| Startup Excellence (Incorporated) | 1       | $20,000    | $5,000            | Virtual Coffee with Google Team + Social Promo |
| Individual / Hobbyist             | 2       | $10,000    | $1,000            | Virtual Coffee with Google Team + Social Promo |
| Best Architectural Design         | 2       | $5,000     | $1,000            | —                                              |
| Best Multimodal UX                | 2       | $5,000     | $1,000            | —                                              |
| Honorable Mentions                | 5       | $2,000     | $500              | —                                              |

```

---
<https://www.youtube.com/watch?v=DCXjvKmUIGY> How to Win the All Things Agentic Hackathon: Judging Criteria Live Q&A | Devpost Build Session 觀看次數：1,558次 2026年8月26日
Google Cloud's Christina Lin (DevRel Engineering Manager) and Willie Turney (Product Marketing Manager) break down exactly what judges look for in the All Things Agentic Hackathon — then answer live submitter questions about their real, in-progress projects. If you're building an autonomous AI agent on Gemini 3.5 and Google's Agent Development Kit for the Taskmaster, Collaborative Partner, or Fortified Enterprise Fleet track, this session covers the judging rubric in detail: what counts as "agentic" vs. just a chatbot with memory, how to prove Google Cloud execution in a 4-minute demo video, what a complete architecture diagram actually needs, and how much detail your README should have. $180,000 in prizes. Submissions close August 31, 2026. TIMESTAMPS 00:00 Welcome & introductions (Devpost, Google Cloud) 02:00 Prize breakdown — $180K total, $50K grand prize 03:14 The three tracks explained: Taskmaster, Collaborative Partner, Fortified Enterprise Fleet 05:41 Judging criteria: README, architecture diagram, demo video 10:06 Live project review: Shipwright — demoing a long-running async agent in 4 minutes 11:16 Live project review: Forever Brain — structuring a demo without overwhelming judges 12:20 Q&A: which track does my project actually fit? 22:07 What "complete" looks like for an architecture diagram 22:44 How long judges actually spend per submission 28:44 Fortified Enterprise Fleet: proving security and governance 35:36 What makes memory "agentic" vs. just a chatbot with recall 39:19 What to include in your README 42:56 Final advice before the deadline Devpost powers hackathons for teams building the future of software. Subscribe for more live build sessions, project reviews, and technical deep dives.
想要贏得全能 Agent 駭客松（All Things Agentic Hackathon），評審們在 Live Q&A 中透露了非常具體的評分重點與致勝策略，主要可以分為三大提交材料的包裝、核心評分標準，以及三大賽道的特定加分項： 一、 三大提交材料的致勝包裝法

1. 展示影片 (Demonstration Video)：最關鍵的第一印象

* 黃金 30 秒法則： 評審接觸專案的第一件事就是看影片，因此必須在影片前 30 秒內創造 "Wow" 的吸睛亮點，抓住評審眼球。
* 嚴格控制在 4 分鐘內： 評審設定了嚴格的計時，絕對不會觀看影片超過 4 分鐘之後的任何內容，因此請務必精簡。
* 影片內容架構： 清楚說明問題痛點與你的解決方案。如果你的 Agent 是需要運行數天或更長的非同步任務（例如 App 審核），請先說明專案，然後直接展示最終運行成果，並可快速滾動日誌（Logs）來證明它確實有在背景執行，評審會看程式碼來驗證。
* 不要使用 AI 配音： 評審強烈建議親自錄音配音，因為 AI 聲音聽起來較缺乏真實感，而評審非常喜愛並看重參賽者的熱情（Energy）。
* 適合大眾傳播： 由於獲勝專案會在 Google Cloud 的社群媒體上推廣，影片風格建議要能讓大眾易於理解與分享。

2. README 說明文件：挖掘深度的橋樑

* 評審在看完影片、產生好奇心後，會深入挖掘你的專案。因此 README 寫得詳細且結構清晰非常重要。
* 內容應包含： 專案的簡短介紹、資料夾結構說明（協助評審快速定位程式碼）、開發過程中的發現與見解（Insights），以及那些你非常自豪、但在 4 分鐘影片中來不及細講的技術亮點與細節。

3. 架構圖 (Architecture Diagram)：清晰易懂

* 評審會根據架構設計與技術棧進行評分。架構圖應保持簡單、 consumable（易於吸收），一眼就能看出 Agent 是如何佈署、元件之間如何連接與協調，切忌塞滿像論文一樣的冗長文字說明。使用 AI 生成架構圖是可以接受的，但必須準確反映實際的架構。
二、 核心評分標準
* 創新性 (Innovation, 佔 40%)： 這是一項關鍵指標。評審看過非常多駭客松專案，因此拒絕普通的聊天機器人（Chatbot）。你的專案必須能超越簡單的問答，展現獨特的 "Wow" 因素。
* 操作可行性 (Operational Utility)： 專案必須真正能運行。評審有內置的工具和系統來測試你的提交，並且會深入研究你的程式碼，驗證它是否真的能達到你所宣稱的功能與效果。
* 架構設計 (Architecture Design)： 設計必須貼合實際需求。例如，若你設計了一個長時運行的 Agent，架構上是否考慮到了失敗恢復步驟（recovery steps）、Token 重試機制、以及持久化資料的儲存方案等。
* Google Cloud 服務的整合（強制性指標）： 這是參賽的必要條件。你必須在專案中實際使用 Gemini 模型、Google ADK 或至少一項 Google Cloud 服務（如 Cloud Run、Cloud SQL、Firestore、Pub/Sub 等）。
三、 三大賽道 (Tracks) 的特定致勝關鍵
* Taskmaster (任務大師賽道)：
  * 旨在尋找能真正替人類自動化解決任務的 Agent。重點在於 Agent 的執行深度與聰明度，而非刻意讓它在雲端持續運行好幾天。
  * 策略： 展示時專注於一個最能驚艷評審（wow the judges）的端到端完整工作流（而非展示多個簡單的 Happy Path 流程），其餘廣泛的應用場景寫在 README 中即可。
* Collaborative Partner (協同合作夥伴賽道)：
  * 核心在於數據的智慧使用（Data collection & Ingestion）。如果僅僅是透過向量檢索來回答，容易被評審視為「只是一個帶有記憶的檢索系統」。
  * 策略： 應更進一步展現 Agent 的主動性，例如利用記憶來進行自我優化（self-improving）、優化與用戶的互動，或甚至觸發外部操作（這能獲得額外加分）。
* Fortified Enterprise (強化企業艦隊賽道)：
  * 聚焦於多 Agent 協同（Swarms）。「安全性（Security）」、「可審計的工作流（Auditable Trail）」與「治理機制」是這個賽道的致勝核心。
  * 策略： 評審更偏好參賽者在實作多 Agent 註冊與運行時，能直接使用 Google Cloud Agent Platform 內建的 Agent Registry。
💡 評審的最後叮嚀 不要過度糾結完美細節，在截止日前**「先提交就對了（submit first）」**，你永遠不知道自己有沒有機會得獎。最重要的是，保持樂趣（Have fun）！

---
