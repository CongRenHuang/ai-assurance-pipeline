# S8 — Cloud Run 部署

**時間盒：** 60 分鐘
**GO/NO-GO：** 非決定項，但**必須在第一週打通**

---

## 為什麼不能留到最後

1. **Hackathon 硬性要求 hosted URL** —— 沒有它直接失格
2. **部署問題永遠比預期久** —— 權限、API 啟用、建置逾時，每一項都可能吃掉半天
3. **越早知道越好** —— 8/19 發現問題有 12 天可解，8/30 發現只剩 1 天

---

## 步驟 1：前置檢查（10 分）

```bash
gcloud --version || echo "❌ 需先安裝 gcloud CLI"
gcloud auth login
gcloud auth application-default login

export PROJECT_ID="你的-project-id"
export REGION="asia-east1"          # 台灣就近；us-central1 亦可
export SERVICE_NAME="assurance-agent"

gcloud config set project $PROJECT_ID

# 啟用必要 API（第一次會等 1-2 分鐘）
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com
```

---

## 步驟 2：API key 進 Secret Manager（10 分）

> ⚠️ **不要用環境變數明文傳 key。** 對一個做資料治理的專案來說，這是最基本的自我要求——而且評審會看。

```bash
source .env
echo -n "$GOOGLE_API_KEY" | gcloud secrets create google-api-key \
  --data-file=- --replication-policy=automatic 2>/dev/null \
  || echo -n "$GOOGLE_API_KEY" | gcloud secrets versions add google-api-key --data-file=-

PROJECT_NUM=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
COMPUTE_SA="${PROJECT_NUM}-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding google-api-key \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/cloudbuild.builds.builder" 2>/dev/null || true

echo "✅ Secret 與權限設定完成"
```

---

## 步驟 3：確認 agent 結構（5 分）

ADK 要求：agent 目錄內有 `agent.py`，且含頂層變數 `root_agent`。

```bash
cat > spike_agent/agent.py <<'PY'
"""Cloud Run 部署進入點。整合 S1/S2/S6 的所有閘門。"""
import os
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents import LlmAgent

MODEL = os.getenv("MODEL", "gemini-3.5-flash")


def assess_release(assessment_id: str, risk_tier: str) -> dict:
    """Assess whether an AI output can be released.

    Args:
        assessment_id: Identifier of the assessment.
        risk_tier: Risk tier, one of R0 R1 R2 R3 R4.
    """
    return {"status": "ASSESSED", "assessment_id": assessment_id,
            "risk_tier": risk_tier}


root_agent = LlmAgent(
    name="assurance_agent",
    model=MODEL,
    instruction=(
        "You are a Release Assessment Agent for a financial AI assurance "
        "pipeline. When asked to assess or release an assessment, call "
        "assess_release with the assessment id and risk tier."
    ),
    tools=[assess_release],
)
PY

cat > spike_agent/__init__.py <<'PY'
from . import agent
PY

cat > requirements.txt <<'PY'
google-adk>=2.7.1
python-dotenv
openinference-instrumentation-google-adk
opentelemetry-sdk
opentelemetry-exporter-otlp-proto-http
PY

# 本機先確認能載入
python -c "from spike_agent.agent import root_agent; print('✅', root_agent.name)"
```

---

## 步驟 4：部署（20 分）

```bash
adk deploy cloud_run \
  --project=$PROJECT_ID \
  --region=$REGION \
  --service_name=$SERVICE_NAME \
  --app_name=assurance_agent \
  --with_ui \
  ./spike_agent 2>&1 | tee evidence/S8-deploy.txt
```

**首次建置約 5–10 分鐘。**

若 `adk deploy` 失敗，用 fallback：

```bash
cat > Dockerfile <<'DOCKER'
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
CMD ["sh","-c","adk api_server spike_agent --host 0.0.0.0 --port $PORT"]
DOCKER

gcloud run deploy $SERVICE_NAME \
  --source . --region $REGION --allow-unauthenticated \
  --set-secrets=GOOGLE_API_KEY=google-api-key:latest \
  --memory=2Gi --timeout=300 2>&1 | tee evidence/S8-deploy-fallback.txt
```

> 註：Dockerfile 用 python:3.13-slim 而非 3.14——3.14 的 slim image 生態可能還不完整，而 ADK 支援 3.10+。本機開發用 3.14 沒問題。

---

## 步驟 5：驗證 hosted URL（15 分）

```bash
export SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION --format='value(status.url)')
echo "SERVICE_URL = $SERVICE_URL" | tee evidence/S8-url.txt

# 健康檢查
curl -sS -o /dev/null -w "HTTP %{http_code}\n" "$SERVICE_URL/"

# 端到端：建 session -> 送訊息
curl -sS -X POST "$SERVICE_URL/apps/assurance_agent/users/u1/sessions/s1" \
  -H 'Content-Type: application/json' -d '{}' | tee evidence/S8-session.json
echo

curl -sS -X POST "$SERVICE_URL/run" -H 'Content-Type: application/json' -d '{
  "app_name":"assurance_agent","user_id":"u1","session_id":"s1",
  "new_message":{"role":"user","parts":[{"text":"Assess assessment ASMT-001, risk tier R3"}]}
}' | tee evidence/S8-e2e.json
```

---

## 通過標準

| # | 驗證 | 必須 |
|---|---|---|
| 1 | 部署成功 | 拿到 `https://...run.app` |
| 2 | 根路徑回應 | HTTP 200（`--with_ui` 時為 UI） |
| 3 | session 可建立 | 回傳 session 物件 |
| 4 | `/run` 端到端可執行 | agent 有回應 |
| 5 | **API key 來自 Secret Manager** | 非明文環境變數 |

---

## 失敗處理

| 症狀 | 處置 |
|---|---|
| `PERMISSION_DENIED` | 確認 compute SA 有 `secretAccessor` 與 `cloudbuild.builds.builder` |
| 建置逾時 | 精簡 `requirements.txt`；`--timeout=1200` |
| `root_agent not found` | 確認 `spike_agent/agent.py` 有頂層 `root_agent`，且 `__init__.py` 有 import |
| Python 版本衝突 | Dockerfile 改 `python:3.12-slim` |
| 冷啟動逾時 | `--min-instances=1`（會產生費用，demo 前再開） |

---

## 💰 費用提醒

Cloud Run 按用量計費，`--min-instances=1` 會持續產生費用。

**建議：** 平時 `--min-instances=0`，錄 demo 影片與提交前一天再調高，避免冷啟動影響評審體驗。提交後記得調回。

```bash
# 錄影/提交前
gcloud run services update $SERVICE_NAME --region=$REGION --min-instances=1
# 之後
gcloud run services update $SERVICE_NAME --region=$REGION --min-instances=0
```

---

## 產出

```
spike_agent/agent.py          ← 部署進入點
requirements.txt
Dockerfile                    ← fallback 時才需要
evidence/S8-deploy.txt
evidence/S8-url.txt           ← ★ hackathon 提交要用
evidence/S8-session.json
evidence/S8-e2e.json
```

> ★ `evidence/S8-url.txt` 裡的 URL 就是 Devpost 提交表單的 **Project URL**。
