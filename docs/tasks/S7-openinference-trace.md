# S7 — OpenInference Decision Trace

**時間盒：** 45 分鐘
**GO/NO-GO：** 非決定項

---

## 為什麼用 OpenInference 而不是自創 span schema

你本來就要做 OTel decision trace，本來就要決定 span 怎麼命名。**用既有標準與自創標準工作量相同**，但前者讓 trajectory 可被任何標準工具讀取。

### 意外紅利：GUARDRAIL 與 EVALUATOR

OpenInference 的 span kind 共十種：

```
LLM · TOOL · AGENT · CHAIN · RETRIEVER
RERANKER · EMBEDDING · GUARDRAIL · EVALUATOR · PROMPT
```

**其中 `GUARDRAIL` 與 `EVALUATOR` 正好是你的核心概念。**

把 policy check 標為 `GUARDRAIL`、evaluation 標為 `EVALUATOR`，等於免費取得語義對齊——稽核工具讀 trace 時能直接辨識這些 span 的性質，不需要自訂慣例。

> 這件事本身有意義：**「這一段執行是在做把關」已經被認為值得在遙測層被標示出來**，而不只是另一個函式呼叫。

---

## 步驟 1：安裝與 tracer 設定（10 分）

```bash
uv pip install openinference-instrumentation-google-adk \
               openinference-semantic-conventions \
               opentelemetry-sdk \
               opentelemetry-exporter-otlp-proto-http

cat > assurance/tracing.py <<'PY'
"""OpenInference tracing + assurance 專用 span 屬性。"""
from __future__ import annotations
import os
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor, ConsoleSpanExporter)

_provider: trace_sdk.TracerProvider | None = None
CAPTURED: list[dict] = []


class CapturingExporter(ConsoleSpanExporter):
    """同時輸出到 console 並保留在記憶體，供測試斷言。"""
    def export(self, spans):
        for s in spans:
            CAPTURED.append({
                "name": s.name,
                "attributes": dict(s.attributes or {}),
                "parent_id": s.parent.span_id if s.parent else None,
                "span_id": s.context.span_id,
            })
        return super().export(spans)


def setup(use_otlp: bool = False, endpoint: str | None = None):
    global _provider
    if _provider:
        return _provider
    _provider = trace_sdk.TracerProvider()

    if use_otlp:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter)
        ep = endpoint or os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:6006/v1/traces")
        _provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(ep)))
    else:
        _provider.add_span_processor(SimpleSpanProcessor(CapturingExporter()))

    from openinference.instrumentation.google_adk import GoogleADKInstrumentor
    GoogleADKInstrumentor().instrument(tracer_provider=_provider)
    trace.set_tracer_provider(_provider)
    return _provider


def tracer():
    return trace.get_tracer("assurance")


# ---- OpenInference span kind 常數 ----
SPAN_KIND = "openinference.span.kind"
GUARDRAIL = "GUARDRAIL"
EVALUATOR = "EVALUATOR"
CHAIN = "CHAIN"


@contextmanager
def guardrail_span(name: str, *, policy_id: str, risk_tier: str,
                   decision: str, override_rejected: bool = False):
    """policy check span，標記為 GUARDRAIL。"""
    with tracer().start_as_current_span(name) as sp:
        sp.set_attribute(SPAN_KIND, GUARDRAIL)
        sp.set_attribute("assurance.policy_id", policy_id)
        sp.set_attribute("assurance.risk_tier", risk_tier)
        sp.set_attribute("assurance.decision", decision)
        sp.set_attribute("assurance.override_rejected", override_rejected)
        yield sp


@contextmanager
def evaluator_span(name: str, *, evaluation: str, score: float, status: str):
    """evaluation span，標記為 EVALUATOR。"""
    with tracer().start_as_current_span(name) as sp:
        sp.set_attribute(SPAN_KIND, EVALUATOR)
        sp.set_attribute("assurance.evaluation", evaluation)
        sp.set_attribute("assurance.score", score)
        sp.set_attribute("assurance.status", status)
        yield sp
PY
echo "✅ assurance/tracing.py"
```

---

## 步驟 2：驗證（20 分）

```bash
cat > tests/test_s7_tracing.py <<'PY'
"""S7: 四個 assurance.* 屬性 + GUARDRAIL/EVALUATOR span kind。"""
import json, pathlib
from assurance import tracing as T

RESULTS = []
def rec(n, ok, d):
    RESULTS.append({"test": n, "passed": ok, "detail": d})
    print(f"{'✅' if ok else '❌'} {n}: {d}")

T.setup(use_otlp=False)

# 模擬一次完整 release assessment
with T.tracer().start_as_current_span("release_assessment") as root:
    root.set_attribute(T.SPAN_KIND, T.CHAIN)

    with T.evaluator_span("eval.citation_coverage",
                          evaluation="citation_coverage",
                          score=0.96, status="PASS"):
        pass

    with T.guardrail_span("policy.source_governance",
                          policy_id="FIN-AI-001", risk_tier="R3",
                          decision="HUMAN_REVIEW"):
        pass

    with T.guardrail_span("policy.hard_block",
                          policy_id="FIN-AI-004", risk_tier="R4",
                          decision="BLOCK", override_rejected=True):
        pass

T._provider.force_flush()
spans = T.CAPTURED

# --- 驗證 ---
names = [s["name"] for s in spans]
rec("1_three_layers_present",
    all(n in names for n in
        ["eval.citation_coverage", "policy.source_governance", "release_assessment"]),
    f"spans={names}")

guard = [s for s in spans if s["attributes"].get(T.SPAN_KIND) == "GUARDRAIL"]
rec("2_guardrail_kind", len(guard) == 2, f"GUARDRAIL span 數={len(guard)}")

ev = [s for s in spans if s["attributes"].get(T.SPAN_KIND) == "EVALUATOR"]
rec("3_evaluator_kind", len(ev) == 1, f"EVALUATOR span 數={len(ev)}")

need = ["assurance.policy_id", "assurance.risk_tier",
        "assurance.decision", "assurance.override_rejected"]
g0 = guard[0]["attributes"] if guard else {}
rec("4_four_custom_attrs", all(k in g0 for k in need),
    f"缺少={[k for k in need if k not in g0]}")

rej = [s for s in guard if s["attributes"].get("assurance.override_rejected")]
rec("5_override_rejected_traced", len(rej) == 1,
    f"override_rejected=True 的 span 數={len(rej)}")

# 父子關係（S9 要用）
root_id = next((s["span_id"] for s in spans
                if s["name"] == "release_assessment"), None)
children = [s for s in spans if s["parent_id"] == root_id]
rec("6_span_tree_intact", len(children) >= 3,
    f"root 底下有 {len(children)} 個子 span（S9 從此抽 trajectory）")

pathlib.Path("evidence").mkdir(exist_ok=True)
pathlib.Path("evidence/S7-results.json").write_text(
    json.dumps({"results": RESULTS,
                "spans": [{"name": s["name"], "attributes": s["attributes"]}
                          for s in spans]},
               indent=2, ensure_ascii=False, default=str), encoding="utf-8")
print("\nPASS" if all(r["passed"] for r in RESULTS) else "\nFAIL")
PY

python tests/test_s7_tracing.py 2>&1 | tee evidence/S7-run.txt
```

---

## 步驟 3（可選，10 分）：本機 trace viewer

```bash
uv pip install arize-phoenix
python -c "import phoenix as px; px.launch_app()" &
sleep 5
# 改用 OTLP 送到 Phoenix
python -c "
from assurance import tracing as T
T.setup(use_otlp=True, endpoint='http://localhost:6006/v1/traces')
print('→ http://localhost:6006 查看 trace')
"
```

> ⚠️ **只用它「看」，不要建 Golden Dataset + Experiments 那套閉環。** 那是持續營運的資產，不是 13 天的東西。截圖給 demo 影片用就好。

---

## 通過標準

| # | 驗證 | 必須 |
|---|---|---|
| 1 | evaluation / policy / root 三層 span 都在 | trace 完整 |
| 2 | GUARDRAIL span kind 正確 | 2 個 |
| 3 | EVALUATOR span kind 正確 | 1 個 |
| 4 | **四個 `assurance.*` 屬性都寫得進去** | ★ 核心 |
| 5 | `override_rejected=True` 進了 trace | S6 的證據可被查詢 |
| 6 | span 父子關係完整 | ★ S9 依賴此 |

---

## 失敗處理

| 症狀 | 處置 |
|---|---|
| instrumentor 與 ADK 2.7.1 不相容 | 退為手動 span（本檔的 `guardrail_span` / `evaluator_span` **本來就是手動的**，不依賴 auto-instrumentor）→ 影響很小 |
| 自訂屬性被吃掉 | 改用 `span.set_attribute` 在 `start_as_current_span` 之後立即設定 |
| span kind 常數名不同 | `from openinference.semconv.trace import SpanAttributes` 查實際常數 |

> **注意：** 這份實作刻意讓 `guardrail_span` / `evaluator_span` **不依賴 auto-instrumentor**。
> 即使 S0 的相容性檢查失敗，S7 仍然能過——auto-instrumentor 只是額外的自動覆蓋層。

---

## 產出

```
assurance/tracing.py
tests/test_s7_tracing.py
evidence/S7-results.json
evidence/S7-run.txt
```
