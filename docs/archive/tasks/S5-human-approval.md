# S5 — Human Approval 走 REST API

**時間盒：** 90 分鐘
**GO/NO-GO：** 非決定項（有 LongRunningFunctionTool 退路）

---

## 為什麼一定要走 API，不用 web UI

Demo 影片裡「reviewer 在自己的介面按核准，agent 恢復執行」比「在 ADK 內建 UI 點一下」有說服力得多，而且那才是 enterprise 的樣子。

**更重要的是：** 走 API 才能證明 approval 是一個**可被系統整合的決策點**，而不是一個人機互動的裝飾。

---

## 已知限制（S0/S5 需確認）

官方文件：confirmation 功能**不支援** `DatabaseSessionService` 與 `VertexAiSessionService`。

**處置：** demo 用 `InMemorySessionService`；`ApprovalDecision` 與 `ControlEvidence` 的持久化寫進**你自己的 evidence store**，獨立於 ADK session。

> 這反而是對的——那是你的 domain object，不該寄生在 framework 的 session 生命週期裡。

---

## 步驟 1：帶結構化 payload 的 approval tool（30 分）

已確認的 API（`tools/function_tool.py:110, 300`）：

```python
FunctionTool(func, require_confirmation=True)        # bool
FunctionTool(func, require_confirmation=callable)    # 動態，可 async
```

```bash
cat > assurance/approval.py <<'PY'
"""Human approval：帶結構化 payload 的 HITL。"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from google.adk.tools import FunctionTool, ToolContext

APPROVAL_LOG: list[dict[str, Any]] = []


def release_assessment(
    assessment_id: str, risk_tier: str, tool_context: ToolContext
) -> dict:
    """Release an AI assessment after human review.

    Args:
        assessment_id: The assessment to release.
        risk_tier: Risk tier R0-R4.
    """
    tc = getattr(tool_context, "tool_confirmation", None)

    if not tc:
        # 第一次呼叫：請求人工確認，帶結構化 payload
        tool_context.request_confirmation(
            hint=(
                f"Assessment {assessment_id} is {risk_tier}. "
                "Reply with: decision(APPROVE/REJECT), reviewer, reason."
            ),
            payload={"decision": "", "reviewer": "", "reason": ""},
        )
        return {"status": "PENDING_HUMAN_APPROVAL",
                "assessment_id": assessment_id, "risk_tier": risk_tier}

    # 恢復執行：讀取人類送回的結構化資料
    payload = tc.payload or {}
    record = {
        "assessment_id": assessment_id,
        "risk_tier": risk_tier,
        "decision": payload.get("decision", "REJECT"),
        "reviewer": payload.get("reviewer", "unknown"),
        "reason": payload.get("reason", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "confirmed_flag": getattr(tc, "confirmed", None),
    }
    APPROVAL_LOG.append(record)
    return {"status": "RELEASED" if record["decision"] == "APPROVE" else "REJECTED",
            **record}


async def needs_confirmation(risk_tier: str = "R0", **_) -> bool:
    """動態門檻：只有 R3 需要人工核准。R4 由 hard policy 直接擋，不進這裡。"""
    return risk_tier == "R3"


release_tool = FunctionTool(release_assessment,
                            require_confirmation=needs_confirmation)
PY
echo "✅ assurance/approval.py"
```

---

## 步驟 2：確認 API 形狀（15 分）

**先用內省確認實際簽章**，不要照抄文件：

```bash
python - <<'PY'
import inspect
from google.adk.tools import FunctionTool, ToolContext

print("FunctionTool.__init__:")
print(" ", inspect.signature(FunctionTool.__init__))
print("\nrequest_confirmation:")
try:
    print(" ", inspect.signature(ToolContext.request_confirmation))
    print(inspect.getdoc(ToolContext.request_confirmation))
except AttributeError as e:
    print("  ⚠️", e)

print("\nToolContext confirmation 相關屬性:")
print(" ", [a for a in dir(ToolContext) if "confirm" in a.lower()])
PY
```

記錄輸出到 `evidence/S5-api-shape.txt`。

---

## 步驟 3：跑起 API server（15 分）

```bash
cat > spike_agent/approval_agent.py <<'PY'
import os
from dotenv import load_dotenv
load_dotenv()
from google.adk.agents import LlmAgent
from assurance.approval import release_tool

root_agent = LlmAgent(
    name="approval_agent",
    model=os.getenv("MODEL", "gemini-3.5-flash"),
    instruction=("You manage AI assessment releases. When asked to release an "
                 "assessment, call release_assessment with the id and risk tier."),
    tools=[release_tool],
)
PY

# 另開一個終端機執行：
adk api_server spike_agent --port 8000
```

---

## 步驟 4：REST 完成 approval（30 分）

```bash
cat > tests/s5_approval_flow.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
BASE=http://localhost:8000
APP=approval_agent
USER=s5
SESSION=sess-s5-001
mkdir -p evidence

echo "== 1. 建立 session =="
curl -sS -X POST "$BASE/apps/$APP/users/$USER/sessions/$SESSION" \
  -H 'Content-Type: application/json' -d '{}' | tee evidence/S5-1-session.json
echo

echo "== 2. 觸發 R3 -> 應回 confirmation 請求 =="
curl -sS -X POST "$BASE/run" -H 'Content-Type: application/json' -d "{
  \"app_name\": \"$APP\", \"user_id\": \"$USER\", \"session_id\": \"$SESSION\",
  \"new_message\": {\"role\":\"user\",\"parts\":[{\"text\":\"Release assessment ASMT-001, risk tier R3\"}]}
}" | tee evidence/S5-2-request.json
echo

echo "== 3. 從輸出找 adk_request_confirmation 的 functionCall.id =="
python - <<'PY'
import json, pathlib, re
raw = pathlib.Path("evidence/S5-2-request.json").read_text()
try: data = json.loads(raw)
except Exception: data = json.loads("[" + re.sub(r"}\s*{", "},{", raw) + "]")
events = data if isinstance(data, list) else [data]
fid = None
for ev in events:
    for p in (ev.get("content") or {}).get("parts") or []:
        fc = p.get("functionCall") or p.get("function_call")
        if fc and "confirmation" in (fc.get("name") or ""):
            fid = fc.get("id"); print("function_call_id =", fid)
pathlib.Path("evidence/S5-fid.txt").write_text(fid or "")
if not fid: print("⚠️  未找到 confirmation 請求——檢查 require_confirmation 是否觸發")
PY

FID=$(cat evidence/S5-fid.txt)
[ -z "$FID" ] && { echo "❌ 無 function_call_id，中止"; exit 1; }

echo "== 4. 送出 APPROVE（純 REST，不碰 web UI）=="
curl -sS -X POST "$BASE/run" -H 'Content-Type: application/json' -d "{
  \"app_name\": \"$APP\", \"user_id\": \"$USER\", \"session_id\": \"$SESSION\",
  \"new_message\": {\"role\":\"user\",\"parts\":[{\"functionResponse\": {
      \"id\": \"$FID\", \"name\": \"adk_request_confirmation\",
      \"response\": {\"confirmed\": true, \"payload\": {
          \"decision\":\"APPROVE\",\"reviewer\":\"dennis\",
          \"reason\":\"Evidence satisfied demo policy.\"}}}}]}
}" | tee evidence/S5-4-approved.json
echo
echo "✅ 檢查 evidence/S5-4-approved.json 是否含 RELEASED 與 reviewer=dennis"
SH
chmod +x tests/s5_approval_flow.sh
./tests/s5_approval_flow.sh 2>&1 | tee evidence/S5-run.txt
```

---

## 通過標準

| # | 驗證 | 必須 |
|---|---|---|
| 1 | R3 觸發 confirmation 請求 | 出現 `adk_request_confirmation` |
| 2 | 動態門檻生效 | R0 不觸發、R3 觸發 |
| 3 | **curl 送出後 agent 恢復執行** | 純 REST，不碰 web UI |
| 4 | `tc.payload` 讀得到結構化資料 | reviewer / decision / reason 都在 |
| 5 | `APPROVAL_LOG` 有完整紀錄 | 可持久化為 ApprovalDecision |

---

## 失敗處理

| 症狀 | 處置 |
|---|---|
| `request_confirmation` 不存在 | 改用 `LongRunningFunctionTool`（見下） |
| SessionService 報錯 | 確認用 InMemory；`adk api_server` 預設即是 |
| 找不到 function_call_id | 改 SSE：`POST /run_sse` 逐事件解析 |
| payload 傳不回來 | 退為 boolean `confirmed`，payload 自行存 evidence store |

**Fallback：LongRunningFunctionTool**

```python
from google.adk.tools import LongRunningFunctionTool

def request_release(assessment_id: str) -> dict:
    """Request release approval. Returns a ticket."""
    return {"status": "PENDING", "ticket_id": f"TKT-{assessment_id}"}

release_tool = LongRunningFunctionTool(func=request_release)
# 外部系統稍後以 functionResponse 帶最終結果恢復
```

成本 +2 小時，仍可 GO。

---

## 產出

```
assurance/approval.py
spike_agent/approval_agent.py
tests/s5_approval_flow.sh
evidence/S5-api-shape.txt
evidence/S5-1..4-*.json
evidence/S5-run.txt
```
