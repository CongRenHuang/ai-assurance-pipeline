# S0 — 環境打通與單點雙殺風險確認

**時間盒：** 30 分鐘
**GO/NO-GO：** 非決定項，但**過不了就直接 NO-GO**（環境都起不來，後面免談）

---

## 目標

1. 確認 ADK 版本與 Python 3.14 相容
2. 打通 Gemini 認證
3. **★ 確認 graph workflow 與 OpenInference auto-instrumentor 相容**（唯一的單點雙殺風險：不相容則 S7 + S9 同時受影響）

---

## 步驟 1：確認版本（3 分）

```bash
cd Project
source .venv/bin/activate

python -c "import google.adk, sys; print('ADK', google.adk.__version__); print('Python', sys.version)"
```

**預期：** `ADK 2.7.1` / `Python 3.14.3`

記錄到 `evidence/S0-versions.txt`：

```bash
mkdir -p evidence
python -c "import google.adk, sys; print('ADK', google.adk.__version__); print('Python', sys.version)" > evidence/S0-versions.txt
uv pip freeze >> evidence/S0-versions.txt
```

> **為什麼要記錄：** 未來 debug 與文章可重現性都需要。ADK 迭代很快，三週後的行為可能不同。

---

## 步驟 2：確認 workflow API 存在（3 分）

```bash
python - <<'PY'
from google.adk.workflow import Workflow, Edge, FunctionNode, START, DEFAULT_ROUTE
print("DEFAULT_ROUTE =", repr(DEFAULT_ROUTE))
print("Edge fields   =", list(Edge.model_fields.keys()))
PY
```

**預期輸出：**
```
DEFAULT_ROUTE = '__DEFAULT__'
Edge fields   = ['from_node', 'to_node', 'route']
```

☑ 若這步失敗 → 你裝到的不是 2.x，`uv pip install -U google-adk`

---

## 步驟 3：確認 template workflow 是否有 deprecation warning（2 分）

```bash
python -W all - <<'PY'
import warnings
warnings.simplefilter("always")
with warnings.catch_warnings(record=True) as w:
    from google.adk.agents import SequentialAgent
    print("SequentialAgent imported OK")
    for x in w:
        print("WARN:", x.category.__name__, x.message)
PY
```

**記錄結果。** 這決定 S3 的退路（fallback 到 SequentialAgent）是否可行。

---

## 步驟 4：Gemini 認證（5 分）

```bash
cat > .env <<'EOF'
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=你的_API_KEY
EOF

cat > .gitignore <<'EOF'
.venv/
.env
__pycache__/
*.pyc
evidence/*.local
EOF
```

> ⚠️ **先寫 .gitignore 再放 key。** 這個順序很重要——一旦 key 進了 git history，清除很麻煩，而且對一個「做資料治理」的專案來說，把 API key commit 上去是最難看的事。

驗證：

```bash
python - <<'PY'
import os
from dotenv import load_dotenv
load_dotenv()
k = os.getenv("GOOGLE_API_KEY", "")
assert k and not k.startswith("你的"), "GOOGLE_API_KEY 未設定"
print("API key loaded, length =", len(k))
PY
```

---

## 步驟 5：確認可用模型（5 分）

```bash
python - <<'PY'
import os
from dotenv import load_dotenv
load_dotenv()
from google import genai
c = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
names = [m.name for m in c.models.list()]
gem = sorted(n for n in names if "gemini" in n)
for n in gem: print(n)
PY
```

**Hackathon 要求 Gemini 3.5+。** 從輸出裡挑一個實際存在的 model id，記錄下來——**後續所有文件的 `MODEL` 常數都用它**。

```bash
# 把你挑的 model id 存起來，後面 spike 共用
echo "MODEL=gemini-3.5-flash" >> .env   # ← 換成實際存在的
```

---

## 步驟 6 ★★★：單點雙殺風險確認（12 分）

**這是 S0 最重要的一步。** 若 graph workflow 與 OpenInference 不相容，S7 與 S9 會同時失效。

```bash
uv pip install openinference-instrumentation-google-adk \
               opentelemetry-sdk \
               opentelemetry-exporter-otlp-proto-http
```

先起一個**本機 span 收集器**（不需要真的 collector，用 console exporter 驗證即可）：

```bash
mkdir -p assurance spike_agent tests evidence
touch assurance/__init__.py spike_agent/__init__.py

cat > evidence/s0_otel_graph_check.py <<'PY'
"""S0 步驟 6：確認 OpenInference instrumentor 能否 instrument graph workflow。"""
import os
from dotenv import load_dotenv
load_dotenv()

from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from openinference.instrumentation.google_adk import GoogleADKInstrumentor

provider = trace_sdk.TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
GoogleADKInstrumentor().instrument(tracer_provider=provider)
print("✅ instrumentor loaded")

from google.adk.workflow import Workflow, Edge, FunctionNode, START, DEFAULT_ROUTE

def classify(text: str) -> str:
    return "R0"

node = FunctionNode(func=classify, name="classify")
wf = Workflow(name="s0_probe", edges=[(START, node)])
print("✅ graph workflow constructed under instrumentation")
print("   nodes:", [n.name for n in wf.graph.nodes] if hasattr(wf, "graph") else "n/a")
PY

python evidence/s0_otel_graph_check.py 2>&1 | tee evidence/S0-otel-graph.txt
```

### 通過標準

- [ ] instrumentor 載入無例外
- [ ] graph workflow 在 instrumentation 生效下能建構

### 若失敗

記錄**確切的錯誤訊息**，然後：

1. 先試 `GoogleADKInstrumentor().instrument()` 不帶 tracer_provider
2. 若仍失敗 → **S7 改為手動 OTel span**（沿用 OpenInference 屬性命名慣例），**S9 改為手動記錄 trajectory**
3. 成本 +2 小時，**仍可 GO**（不是決定項）

> **重點：失敗不是災難，未知才是。** 現在知道要 +2 小時，好過在 8/28 才發現。

---

## S0 檢核表

- [ ] ADK 版本記錄到 `evidence/S0-versions.txt`
- [ ] `Workflow / Edge / DEFAULT_ROUTE` import 成功
- [ ] SequentialAgent deprecation 狀態已記錄
- [ ] `.gitignore` **先於** `.env` 建立
- [ ] API key 載入成功
- [ ] 可用 Gemini model id 已確認並寫入 `.env`
- [ ] ★ OpenInference + graph workflow 相容性已測，結果記錄

---

## 產出

```
evidence/S0-versions.txt
evidence/S0-otel-graph.txt
.env  .gitignore
assurance/  spike_agent/  tests/  evidence/
```
