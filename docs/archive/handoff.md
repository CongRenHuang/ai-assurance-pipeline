# Release Assessment Agent — 交接文件

**寫給：** 下一個 session 的自己（或 Claude）
**時間：** 2026-08-31 23:10（台北）
**取代：** 同日上午那一版（其「影片已錄」「main 齊平」「`00005-qnc`」三項皆已失效）
**Repo：** https://github.com/CongRenHuang/ai-assurance-pipeline ← **已轉 public**
**Live：** https://assurance-agent-6eqpujphvq-de.a.run.app

---

## 一、現在的狀態

**All Things Agentic Hackathon** 提交（截止 2026-09-01 08:00 台北，**剩約 8.8 小時**）。

| 項目 | 狀態 |
|---|---|
| 賽道 | **The Taskmaster** |
| Repo 可見性 | **Public**（今晚才轉；先前未登入看是 404，評審會直接撞牆） |
| 影片 | 🔴 **需重錄** — 已錄的那支用的是 v1 腳本，宣稱了五項 repo 沒有的功能 |
| Devpost | draft，**尚未正式送出** |
| Repo 同步 | `main` **ahead 5，尚未 push** |
| Cloud Run | `assurance-agent-00006-w8l`，`--min-instances=1`，asia-east1，project `ai-nursing-simulator` |
| 腳本 | `docs/demo-script-v3.md`（v1/v2 皆已作廢） |

**進度停在 WS8 完成、WS9（錄影）尚未開始。**

---

## 二、專案是什麼

**Release Assessment Agent** — 把 AI 產出的證據轉成可辯護的放行／不放行決策。

不是治理（不定義政策邊界），不是可觀測性（不只產生訊號），**是決策層**：
決定什麼可以放行、根據什麼、留下什麼證據，而且**即使有核准權限的人說 yes 也拒絕放行**。

### 核心設計主張

1. **LLM 只做 triage，永不決定放行**
2. **Fail-closed 貫穿每一層** — 包括自主性本身：planner 失敗時跑「全部」四項檢查
3. **執行軌跡是評估契約的一部分** — 還要看是「哪個元件」做的決定

### ★ 第 4 條（今晚新增，實測得出，不是設計出來的）

**LLM 的變異被結構性地關在一個「不是放行決策」的邊界裡。**

三次獨立跑（其中一次 planner 完全停擺），以 **assessment id** 逐一比對：

```
A54 S28 H9 B9   ← e7b7876 committed
A43 S39 H9 B9   ← 無 key，fail-closed 全跑
A59 S23 H9 B9   ← 現為 canonical
```

| | 三次是否同一組 |
|---|---|
| HUMAN_REVIEW 9 筆 | **YES** `002 003 030 052 074 076 085 088 095` |
| BLOCK 9 筆 | **YES** `014 023 040 067 071 094 097 099 100` |
| AUTO∪SAMPLE 82 筆 | **YES** |

只有 AUTO/SAMPLE 的界線會動 —— 而兩者都是放行，SAMPLE 只是抽樣稽核。

**機制：** `SAMPLE` 條件是 `min_score < LOW_CONFIDENCE_THRESHOLD (0.8)`，
`min_score` 取決於 planner 選了哪些 evaluator；WARN/FAIL 是個別 evaluator 的
判定，不因多跑幾個而消失。

證據：`evidence/S2-planner-variance.json`

> ⚠️ **四類計數不可重現，不要再宣稱它可重現。** README 原本寫
> 「Counts are reproducible」，那是錯的宣稱，今晚已刪。可宣稱的是
> `H9 / B9 / 82`。

⚠️ **兩個 82 是不同的量。** 「82 筆」是量測的路由計數；「82% 時間減幅」是估計值，
數字接近純屬這份語料的巧合。**不要混為一談。**

---

## 三、關鍵技術事實（不要重新發現）

### ADK plugin 層 vs agent 層的短路差異

| 層 | 短路條件 | 後果 |
|---|---|---|
| Plugin (`plugin_manager.py:307`) | `result is not None` | 空 dict **會**擋 |
| Agent (`llm_flows/functions.py:621`) | `if function_response:` truthy | 空 dict **不會**擋，靜默通過 |

→ 硬性政策必須放 plugin 層。

### 沒有使用 ADK Graph Workflow

`assurance/policy.py::route_item()` 是純 Python `if`/`elif` 鏈。
**評估過但沒採用** —— 未匹配路由時會靜默結束分支。
⚠️ **不存在 `tests/test_s3_*`**，不要引用 S3 測試。
（本機 `abandoned/graph-workflow` 分支留有當初那條被放棄的實作。）

### Policy ID

`FIN-AI-000~004` plugin 層 · `FIN-AI-005~010` batch router · `FIN-AI-011` sovereignty

### planner 的輸入只有 `content` 一個字串

`plan_for(content)` 看不到 `numeric_claims` / `claimed_sources` 等欄位 ——
它是從句子本身判斷該跑哪些檢查。這件事讓「skipped the numeric check because
this answer makes no numeric claim」這句旁白站得住，但也表示**選擇逐跑不保證**。

### 部署陷阱

- `adk deploy cloud_run` **不打包 sibling package** → 用 `gcloud run deploy --source .`
- API 的 `app_name` 是**資料夾名**（`deploy_agent`）
- **`revision 00001` = 新建服務，不是新版本。** 互動式問 unauthenticated 也是同一個訊號
- 本機 `.venv` 是 macOS arm64；Cowork 的 Linux 沙箱跑不了，ADK 測試只能在你自己的終端機跑

---

## 四、什麼跑在哪裡（誠信要點）

| 元件 | 位置 |
|---|---|
| `release_assessment` agent + `HardPolicyGate`（R4 拒絕覆寫，回應自帶 trajectory） | **Cloud Run 已部署** `00006-w8l` |
| `/.well-known/agent.json` | **Cloud Run 已部署** |
| `assurance.batch` 100 筆管線 | **本機執行**，輸出 committed |
| `SovereigntyGatePlugin` | **已寫，未部署**（未註冊進 live plugin chain） |

**這張表是誠信的核心。** README 的「What runs where」章節就是它。

---

## 五、文件結構

```
README.md                       ← 指標卡以 9/9/82 不變量領頭
docs/architecture.md            ← mermaid + 說明（已改為只引用不變量）
docs/decision-log.md
docs/baseline-estimate.md
docs/demo-script-v3.md          ← ★ 錄影就看這一份
docs/assets/architecture.png
docs/archive/
  handoff.md                    ← 本檔
  final-22-hours-plan.md        ← WS0–WS10，含各 GATE 結果
  devpost-submission.md         ← Devpost 草稿
  demo-script.md                ← v2，頂端有 SUPERSEDED 橫幅
evidence/
  S2-batch-run.json             ← canonical（A59 那次）
  S2-batch-run.nokey.json       ← fail-closed 那次
  S2-planner-variance.json      ← ★ 不變量宣稱的證據
```

---

## 六、Next moves

### 🔴 立即

- [ ] **`git push origin main`** —— 5 筆未推，repo 公開但評審看到的是舊版
- [ ] **刪掉誤建的 Cloud Run 服務**（掛著 `--min-instances=1` 在燒錢）
      `gcloud run services delete assurance-agent --region=asia-east1 --project=openai-error-archaeologist`
- [ ] **WS9 錄影**（照 `docs/demo-script-v3.md`，六段、旁白約 528 words）
      - 開錄前跑一次：確認 ASMT-034 的 planner 仍略過 `numeric_claim_check`
        （不中就換 `source_ttl` 那一類，30 筆可選）
- [ ] **無痕視窗確認影片真的公開** —— 唯一「以為好了但沒公開」會直接失格的項目
- [ ] **Devpost 正式送出** —— Category = **The Taskmaster**，填影片／repo／Live／架構圖

### 🟡 已決定不做

**Cloud Run Job 加分題 —— 放棄。** 三個理由：

1. 它的 **GATE C「雲端計數與本機一致」建立在已被推翻的前提上** ——
   四類計數本機自己就跑不出同一組。照原規則「任一 GATE 沒過就停手」，就是停。
2. **會傷到最強的一鏡。** v3 的 S2 靠兩個終端機並排跑本機批次來показ fail-closed
   對照，Job 執行頁做不到。「只需重錄 40 秒」是 v2 六場結構下的估計。
3. `cloud-run-job-guide.md` **不在 repo 裡**，GATE A/B 等於從零。

留到提交後當評審期加分素材。

### ⚪ 提交後

- [ ] `--min-instances=0`（等評審期結束）
- [ ] Bonus：Medium 文章 + `#AllThingsAgenticHackathon`
      （`iThome-Day2-draft.md` 已刪；鐵人賽是獨立承諾，**不要為 bonus 綁上去**）

---

## 七、工作原則

1. **Commit 只能是 Dennis Huang 一人作者，無 Claude 署名**
   （repo 已設 local `user.name`／`user.email`，工作機的 global 是
   `developerhygiea@hygieaai.com`，**換機器要先確認**）
2. **永遠回覆繁體中文**
3. **回答前先釐清問題本質，查證再答**
4. **畫面上每個數字、ID、JSON key 都要能在 `evidence/` 或 `data/` 搜到**
5. **估計值必須標明為估計**，免責聲明由模組常數組出，結構上不可省略
6. **OWASP 只宣稱 ASI01 / ASI03**，不宣稱法遵認證，只用合成資料
7. **腳本與實作衝突時，改腳本，不改事實**

---

## 八、教訓

**語料參數必須對齊 evaluator 門檻。** `max_age_days=110` vs `SOURCE_TTL_DAYS=90`。
第一次修正（110→75）清掉 FAIL 線但遺漏 WARN 線（90×0.7=63d），第二次（75→55）
才補齊。**同一個 bug 修了兩次，因為第一次只看了一半。**

**DoD 可能建立在錯誤前提上。** WS7-4 寫「確認四類計數仍是 A54 S28」——
它沒過，而沒過的方式比過了更有價值。**當驗證失敗時，先問「這條驗證本身對嗎」，
再問「哪裡壞了」。**

**先讓權威產物落地，再做選配的呈現。** `batch.py` 原本先 `render_packet()`
再寫 `evidence/`，而 `render_packet` 對非 HUMAN_REVIEW/BLOCK 會拋例外 ——
一次例外就丟掉整整 7 分鐘的跑。

**`git commit --amend` 會把 index 裡既有的東西一起摺進去。** 今晚一筆
「文件重整」的 commit 因此吞掉了三個 FIX 與兩份 evidence，訊息完全沒提。
未推之前 `git reset` 重切即可，**推出去就來不及了**。

**部署前先確認 `gcloud config get-value project`。** 今晚 FIX-2 第一次部到
`openai-error-archaeologist`，在那裡新建了一個服務，而所有文件指向的
`ai-nursing-simulator` 那個完全沒被更新。

**三次賽道搖擺。** Taskmaster → Fortified → Taskmaster。真正的變數不是評審信，
是 WS5 語料修正。教訓是**先有自己的判斷，再看外部意見**。
