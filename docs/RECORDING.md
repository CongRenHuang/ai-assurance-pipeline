# 錄影執行手冊 — 從頭跟到尾

**這一份是拍攝時唯一要開的檔。** 由上往下做。

- 旁白她看：https://claude.ai/code/artifact/420123dc-9161-437c-be0d-7f151ac53574
- `docs/demo-storyboard.md`、`docs/demo-script-v3.md` 是**參考資料**，拍的時候不用翻
- 旁白已預錄成六段 mp3：`docs/assets/segments/S1.mp3` ~ `S6.mp3`（ElevenLabs，實測共 196.7 秒）

---

# 第一部分 · 自動化流程（S1~S5 一鏡到底，只有 S6 要手）

`scripts/demo_recorder/` 是整套 driver：`prerun.py` 錄影前先真的跑一次批次與
Cloud Run，把結果存成 `docs/assets/takes/take-config.json` 與 `batch.log`；
`player.py` 錄影時照旁白時間軸自動重播 / 真跑對應指令，**S1 到 S5（0:00–3:24）
全程不用碰鍵盤**，只有 S6 的兩個瀏覽器鏡頭要手動操作。

## 0. 五秒試片（第一次用、或换了螢幕/主題後都要重跑）

```bash
cd ~/Project/ai-assurance-pipeline && source .venv/bin/activate && export PYTHONPATH=.
python -m scripts.demo_recorder.player --test 5
open docs/assets/takes/test.mov
```

開檔確認四件事：螢幕錄製權限沒跳窗擋畫面、游標有進畫面、`REVERSE-VIDEO SAMPLE`
那行真的反白、cyan/green 顏色沒掉。**任一項不過，全程改用 `--no-capture`
+ 手動開 QuickTime**（見第三部分附錄，流程其餘步驟不變）。

## 1. 環境確認

- 終端機：字體 ≥ 16pt、視窗寬度 ≥ 100 字元（S5 免責聲明是一長行）、深色主題、
  關閉通知、隱藏書籤列，螢幕上不得出現 API key / `.env` / 個資
- 桌面清乾淨（`screencapture` 錄整個螢幕，桌面圖示、Dock 通知都會入鏡）
- `gcloud config get-value project` 要是 `ai-nursing-simulator`
- `git status --short` 要乾淨

## 2. Prerun（錄影前跑一次，這是唯一一次寫 `evidence/`）

```bash
python -m scripts.demo_recorder.prerun
```

跑完約 7–8 分鐘（Gemini + 100 筆批次 + Cloud Run 暖機）。做的事：

1. 找一個 planner 會略過 `numeric_claim_check` 的 ID（S2 用）
2. 確認同一筆在無 key 時 fallback 到全部四項（S2 用）
3. 真跑一次批次（`--packet ASMT-088`），stdout tee 到 `docs/assets/takes/batch.log`，
   逐行時間戳存到 `batch.timing.jsonl`（S2/S3/S4/S5 靜態鏡的資料來源，**這是全程
   唯一一次寫 `evidence/S2-batch-run.json`**）
4. 建 Cloud Run session、確認 agent card 200、送一次暖身 R4 請求（讓 S6 撈 log
   時不會因為 ingestion lag 撈不到）

全部寫進 `docs/assets/takes/take-config.json`。

**跑完檢查**：`take-config.json` 裡 `planner.selected_evaluators` 不含
`numeric_claim_check`；`batch.batch.packet_has_full_packet` 是 `true`
(若是 `false`，S4 畫面改用 `batch.fallback_human_review_id`，旁白不用改字，
因為旁白從沒念過 ID)。

## 3. 乾跑一次確認時間軸

```bash
python -m scripts.demo_recorder.player --dry-run
```

確認 TOTAL ≤ 4:00。第一次用某個 segment 時可以先校準節奏：

```bash
python -m scripts.demo_recorder.player --segment S2 --calibrate
```

邊聽 mp3 邊看碼表，把想要的分鏡秒數記下來，微調 `scripts/demo_recorder/scenes.py`
裡對應段的 `S2_ORIG` 等字典（一次性工作，調好之後不用再動）。

## 4. 正式錄

```bash
python -m scripts.demo_recorder.player
```

driver 自己開 `screencapture -v`、播六段旁白到你的耳機對點、依序真跑 S1~S5 的畫面。
**你唯一要做的事**：

1. 聽到「S1..S5 done. Manual S6 now」提示，切到瀏覽器，按 Enter 記錄時間點
2. 照 S6 分鏡手動操作（下面「S6 手動步驟」）
3. 結束卡念完停 2 秒，錄影會由 `-V` 自己在時限到時停止（用 `--no-capture` 則自己按停止）

### S6 手動步驟（唯一要手動的 32 秒）

1. 分頁 1：`https://assurance-agent-6eqpujphvq-de.a.run.app/.well-known/agent.json`，
   **網址列的 `.run.app` 要清楚入鏡**
2. 分頁 2：Cloud Console → Logs Explorer，查詢已預先貼好（見下），按下 **Run**：
   ```
   resource.type="cloud_run_revision"
   resource.labels.service_name="assurance-agent"
   jsonPayload.name="policy.hard_block"
   ```
3. Highlight 撈出來那筆的六行屬性：
   ```
   "name": "policy.hard_block"
   "openinference.span.kind":     "GUARDRAIL"
   "assurance.policy_id":         "FIN-AI-004"
   "assurance.decision":          "BLOCK"
   "assurance.override_rejected": true
   "assurance.plugin":            "HardPolicyGate"
   "assurance.plugin_index":      2
   ```
4. 結束卡：專案名 + GitHub URL + `#AllThingsAgenticHackathon`，**停 2 秒**

> 這一撈是撈 prerun 暖身請求或步驟 4 錄影時 S3 那次真實請求都可以 —— 兩次都是
> 真的打 `HardPolicyGate`，log 內容一樣。暖身請求先送過，ingestion lag 不會卡住你。

## 5. Mux 音軌

```bash
bash docs/assets/takes/mux.sh
open docs/assets/takes/final.mov   # 無痕視窗確認音畫同步、無雜音
```

`mux.sh` 是 `player.py` 收工時自動產生的，把 `take.mov` 與六段 mp3 依
`take-timeline.json` 記錄的真實 offset 貼上去 —— **不用剪接對嘴**。
S6 那段的 offset 是你在步驟 4 按 Enter 那一刻記下的，其餘五段是 driver 自己
算出的常數。

---

# 第二部分 · 錄完

## 1. 先 commit 拍攝那次的證據

```bash
cd ~/Project/ai-assurance-pipeline
git add evidence/S2-batch-run.json
git commit -m "chore: evidence from the filmed batch run"
git push origin main
```

**這一步不能省。** 影片裡的數字要能在 repo 搜到，這是紅線第 1 條。

## 2. 剪接

- `docs/assets/takes/final.mov` 已經是 S1→S6 正確順序、音畫同步，可直接進剪接軟體
- 總長 **≤ 4:00**
- 加英文字幕

## 3. 上傳

- YouTube 或 Vimeo，**設為公開**（不是不公開、不是未列出）
- 🔴 **開無痕視窗確認影片真的能播** ← 唯一「以為好了但沒公開」會直接失格的項目
- 處理可能要好幾小時，**早點傳**

## 4. Devpost

- Project details → 貼上影片 URL
- 最後按 **Submit**

## 5. 送出之後

- **不要再推 repo、不要換影片、不要改 Cloud Run 設定**，直到 **10/09 公布得獎**
- `--min-instances=0` 也等到那時候再做

---

# 第三部分 · 附錄：全手動備援

driver 或 `screencapture` 出狀況時的備援方案：`player.py` 全部指令加
`--no-capture` 改用 QuickTime；`prerun.py` 照跑不受影響（它本來就不碰螢幕錄影）。
若整套 driver 都要放棄，改回逐指令手動操作，指令都在
`docs/demo-storyboard.md` Part C「拍攝指令總表」（`SHOT-CMD-A/B/Q/MAIN/R4/RESOLVE/VAR`），
分鏡秒數對照見同檔 Part B。三個終端機分頁（T1 批次、T2 無 key 對照、T3 Cloud Run +
resolve）的開法：

```bash
cd ~/Project/ai-assurance-pipeline && source .venv/bin/activate && export PYTHONPATH=. && export PS1='$ '
```

流程與紅線不變：**整晚只有一次批次跑會寫 `evidence/`**，S3 一定要在 S6 之前拍
（Cloud Logging 那筆 log 要留給 S6 撈），旁白稿全文在 `docs/demo-narration.md`。
