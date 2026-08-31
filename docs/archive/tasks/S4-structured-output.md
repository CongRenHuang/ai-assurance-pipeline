# S4 — 結構化 Domain Object（已知陷阱）

**時間盒：** 60 分鐘
**GO/NO-GO：** 非決定項

---

## 已知限制

官方文件：`output_schema` 與 `tools` 同時使用「only supported by specific models」，其他模型「may not work reliably」。

**這個限制在推你走正確的架構：**

| Evaluator 類型 | 實作方式 | 需要 output_schema？ |
|---|---|---|
| **Deterministic**（citation 覆蓋率、hash 比對、TTL） | 純 Python 函式 | ❌ 根本不需要 |
| **Model-based**（groundedness 判斷） | `LlmAgent` + `output_schema`，**不掛 tool** | ✅ |

> 框架限制**強制**了你的 deterministic-first 原則。這不是妥協，是框架和你的設計原則剛好一致。

---

## 步驟 1：Domain Object Schema（15 分）

```bash
cat > assurance/schema.py <<'PY'
"""四個核心 domain object。Pydantic 保證結構，不依賴 LLM 自律。"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field

RiskTier = Literal["R0", "R1", "R2", "R3", "R4"]
Decision = Literal["AUTO", "SAMPLE", "HUMAN_REVIEW", "BLOCK"]


class EvaluationResult(BaseModel):
    evaluation: str = Field(description="評估項目名稱，如 citation_coverage")
    score: float = Field(ge=0.0, le=1.0, description="0.0-1.0 分數")
    status: Literal["PASS", "FAIL", "WARN"]
    evaluator_version: str = "0.1.0"
    rationale: str = Field(description="一句話說明判定理由")


class RiskDecision(BaseModel):
    operation: str
    risk_tier: RiskTier
    decision: Decision
    policy_id: str
    required_controls: list[str] = Field(default_factory=list)


class ApprovalDecision(BaseModel):
    decision: Literal["APPROVE", "REJECT"]
    reviewer: str
    reason: str
    timestamp: str


class Transformation(BaseModel):
    """v0.2 Sensitive Data Boundary 預留欄位。v0.1 固定為 none。

    不用 `anonymized: bool` 的理由：GDPR 下 pseudonymization（Art.4(5)，
    仍屬 personal data）與 anonymization（Recital 26，不再適用）法律效果
    不同，單一布林值無法表達可逆性與 mapping 存放位置。
    """
    type: Literal["none", "redaction", "pseudonymization", "anonymization"] = "none"
    reversible: Optional[bool] = None
    mapping_location: Optional[str] = None
    note: str = "v0.1 uses synthetic data only; no de-identification applied"


class ControlEvidence(BaseModel):
    control_id: str
    test: str
    result: Literal["PASS", "FAIL", "BLOCKED", "OVERRIDE_REJECTED"]
    evidence_ref: str
    trajectory: list[str] = Field(default_factory=list, description="S9 填入")
    transformation: Transformation = Field(default_factory=Transformation)
PY
python -c "
from assurance.schema import ControlEvidence
import json
e = ControlEvidence(control_id='DEMO-AI-001', test='citation_coverage',
                    result='PASS', evidence_ref='sha256:abc')
print(json.dumps(e.model_dump(), indent=2, ensure_ascii=False))
"
```

---

## 步驟 2：穩定度測試（30 分）

```bash
cat > tests/test_s4_output_schema.py <<'PY'
"""S4: output_schema 穩定度（20 次）+ tools 相容性探測。"""
import asyncio, json, os, pathlib
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types
from pydantic import ValidationError

from assurance.schema import EvaluationResult

MODEL = os.getenv("MODEL", "gemini-3.5-flash")
N = 20

SAMPLE = """Answer: 依內規第 3.2 條，申請需附身分證影本與財力證明。
Sources: [doc_A p.12]
Claim without citation: 申請通常 3 個工作天核准。"""


async def run(agent, prompt):
    r = InMemoryRunner(agent=agent)
    s = await r.session_service.create_session(app_name=r.app_name, user_id="s4")
    out = []
    async for ev in r.run_async(user_id="s4", session_id=s.id,
        new_message=types.Content(role="user", parts=[types.Part(text=prompt)])):
        if ev.content and ev.content.parts:
            for p in ev.content.parts:
                if p.text: out.append(p.text)
    return "".join(out)


async def main():
    results = {"ok": 0, "fail": 0, "errors": [], "samples": []}

    agent = LlmAgent(
        name="evaluator", model=MODEL,
        instruction=("You are a citation-coverage evaluator. Score 0.0-1.0 for "
                     "what fraction of claims carry a citation. Respond ONLY "
                     "with the required JSON."),
        output_schema=EvaluationResult,
        output_key="eval_result",
        # 刻意不掛 tools —— 這是 deterministic-first 的架構選擇
    )

    for i in range(N):
        try:
            txt = await run(agent, SAMPLE)
            obj = EvaluationResult.model_validate_json(txt.strip())
            results["ok"] += 1
            if i < 3: results["samples"].append(obj.model_dump())
        except (ValidationError, ValueError, json.JSONDecodeError) as e:
            results["fail"] += 1
            results["errors"].append(f"run{i}: {type(e).__name__}: {str(e)[:120]}")
        print(f"  {i+1}/{N} ok={results['ok']} fail={results['fail']}", end="\r")

    rate = results["ok"] / N
    print(f"\n\nschema 通過率: {results['ok']}/{N} = {rate:.0%}")
    print("✅ >=95%，直接用" if rate >= 0.95 else
          "⚠️  80-95%，加 retry wrapper (+2h)" if rate >= 0.80 else
          "❌ <80%，改自由文字 + 確定性 parser (+3h)")

    # 探測：掛 tools 會怎樣
    try:
        def dummy(x: str) -> dict:
            """A dummy tool."""
            return {"ok": True}
        a2 = LlmAgent(name="probe", model=MODEL, instruction="Evaluate.",
                      output_schema=EvaluationResult, tools=[dummy])
        t = await run(a2, SAMPLE)
        EvaluationResult.model_validate_json(t.strip())
        results["with_tools"] = "unexpectedly worked"
    except Exception as e:
        results["with_tools"] = f"{type(e).__name__}: {str(e)[:150]}"
    print(f"\n掛 tools 探測: {results['with_tools']}")

    results["pass_rate"] = rate
    pathlib.Path("evidence").mkdir(exist_ok=True)
    pathlib.Path("evidence/S4-results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")


asyncio.run(main())
PY

python tests/test_s4_output_schema.py 2>&1 | tee evidence/S4-run.txt
```

---

## 通過標準

| 通過率 | 處置 | 成本 |
|---|---|---|
| **≥ 95%** | 直接用 | 0 |
| 80–95% | 加 retry wrapper | +2h |
| < 80% | 改自由文字 + 確定性 parser | +3h |

**任何結果都不影響 GO/NO-GO。** 你的 deterministic evaluator 根本不需要這個機制。

---

## 步驟 3：Deterministic Evaluator 對照（15 分）

證明主力 evaluator 完全不需要 LLM：

```bash
cat > assurance/evaluators.py <<'PY'
"""Deterministic evaluators：純函式，100% 可重現，零 LLM。"""
from __future__ import annotations
import hashlib, re
from datetime import datetime, timezone
from assurance.schema import EvaluationResult

CITED = re.compile(r"\[[^\]]+\]")


def citation_coverage(answer: str) -> EvaluationResult:
    sentences = [s.strip() for s in re.split(r"[。.\n]", answer) if s.strip()]
    if not sentences:
        return EvaluationResult(evaluation="citation_coverage", score=0.0,
                                status="FAIL", rationale="no content")
    cited = sum(1 for s in sentences if CITED.search(s))
    score = cited / len(sentences)
    return EvaluationResult(
        evaluation="citation_coverage", score=round(score, 4),
        status="PASS" if score >= 0.8 else "FAIL",
        rationale=f"{cited}/{len(sentences)} sentences carry a citation",
    )


def content_integrity(content: str, expected_sha256: str) -> EvaluationResult:
    actual = hashlib.sha256(content.encode()).hexdigest()
    ok = actual == expected_sha256
    return EvaluationResult(
        evaluation="content_integrity", score=1.0 if ok else 0.0,
        status="PASS" if ok else "FAIL",
        rationale=f"sha256 {'match' if ok else 'MISMATCH'}",
    )


def source_ttl(fetched_at_iso: str, max_age_days: int = 90) -> EvaluationResult:
    age = (datetime.now(timezone.utc)
           - datetime.fromisoformat(fetched_at_iso)).days
    ok = age <= max_age_days
    return EvaluationResult(
        evaluation="source_ttl", score=1.0 if ok else 0.0,
        status="PASS" if ok else "FAIL",
        rationale=f"age={age}d, limit={max_age_days}d",
    )
PY

python - <<'PY'
from assurance.evaluators import citation_coverage, content_integrity
r = [citation_coverage("依內規第 3.2 條 [doc_A p.12]。申請 3 天核准。") for _ in range(100)]
assert all(x == r[0] for x in r), "不確定！"
print("✅ 100 次結果完全一致：", r[0].model_dump())
print("✅ deterministic evaluator 零 LLM、零 schema 風險")
PY
```

---

## 產出

```
assurance/schema.py         ← 含 transformation 預留欄位
assurance/evaluators.py
tests/test_s4_output_schema.py
evidence/S4-results.json
evidence/S4-run.txt
```
