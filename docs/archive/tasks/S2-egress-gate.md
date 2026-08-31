# S2 ★ — Egress Gate（LLM 呼叫攔截）

**時間盒：** 30 分鐘
**GO/NO-GO：** ★★★ **決定項**

---

## 目標

S1 擋的是 **tool egress**（資料出去）。S2 擋的是 **model egress**（資料進到外部模型）。

這是兩個不同的邊界。S1 過了不代表 S2 會過。

```text
SENSITIVE 資料
     ↓
before_model_callback  ← S2 在這裡攔截
     ↓
Cloud LLM              ← 必須「完全沒有被呼叫」
```

---

## ⚠️ 驗證方法是這個 spike 的重點

**不可以只看回應文字判斷。**

回應文字看起來正確，不代表請求沒有送出去。這正是你專案在講的「200 OK 不代表答對了」的同構問題——**BLOCKED 的文字不代表資料真的沒外送**。

必須用**呼叫計數**驗證：包裝 model 物件，計算 `generate_content` 實際被呼叫幾次。

---

## 步驟 1：擴充 Plugin（10 分）

```bash
cat >> assurance/plugin.py <<'PY'


# ---------- S2: Egress Gate ----------
SENSITIVE_MARKERS = ("[SENSITIVE]", "身分證", "帳號", "CONFIDENTIAL")

COUNTERS.setdefault("model_callback", 0)
COUNTERS.setdefault("model_blocked", 0)


def _extract_text(llm_request) -> str:
    """從 LlmRequest 抽出所有文字，用於敏感標記偵測。"""
    chunks = []
    for c in getattr(llm_request, "contents", None) or []:
        for p in getattr(c, "parts", None) or []:
            t = getattr(p, "text", None)
            if t:
                chunks.append(t)
    return "\n".join(chunks)


class EgressGatePlugin(BasePlugin):
    """阻止 SENSITIVE 內容進入外部模型。"""

    def __init__(self) -> None:
        super().__init__(name="egress_gate")

    async def before_model_callback(self, *, callback_context, llm_request):
        from google.genai import types
        COUNTERS["model_callback"] += 1
        text = _extract_text(llm_request)
        hit = [m for m in SENSITIVE_MARKERS if m in text]
        if hit:
            COUNTERS["model_blocked"] += 1
            return types.Content(
                role="model",
                parts=[types.Part(text=(
                    "BLOCKED by FIN-AI-003: sensitive content must not be sent "
                    f"to an external model. markers={hit}"
                ))],
            )
        return None
PY
echo "✅ EgressGatePlugin 已附加"
```

---

## 步驟 2：可計數的 Model 包裝（10 分）

```bash
cat > tests/counting_model.py <<'PY'
"""包裝真實 model，計算 generate_content 實際被呼叫次數。

這是 S2 的證據來源——不依賴回應文字，直接數 API 呼叫。
"""
from google.adk.models.google_llm import Gemini

CALLS = {"generate_content": 0}


class CountingGemini(Gemini):
    async def generate_content_async(self, llm_request, stream=False):
        CALLS["generate_content"] += 1
        async for r in super().generate_content_async(llm_request, stream=stream):
            yield r


def reset():
    CALLS["generate_content"] = 0
PY
echo "✅ tests/counting_model.py"
```

---

## 步驟 3：驗證（10 分）

```bash
cat > tests/test_s2_egress_gate.py <<'PY'
"""S2: 證明 SENSITIVE 內容完全沒有觸發 LLM 呼叫。"""
import asyncio, json, os, pathlib
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from assurance.plugin import EgressGatePlugin, COUNTERS, reset_counters
from tests.counting_model import CountingGemini, CALLS, reset as reset_calls

MODEL = os.getenv("MODEL", "gemini-3.5-flash")
RESULTS = []


async def run(prompt: str) -> str:
    reset_counters(); reset_calls()
    agent = LlmAgent(name="egress_probe", model=CountingGemini(model=MODEL),
                     instruction="You are a helpful assistant.")
    runner = InMemoryRunner(agent=agent, plugins=[EgressGatePlugin()])
    s = await runner.session_service.create_session(
        app_name=runner.app_name, user_id="s2")
    out = []
    async for ev in runner.run_async(
        user_id="s2", session_id=s.id,
        new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
    ):
        if ev.content and ev.content.parts:
            for p in ev.content.parts:
                if p.text: out.append(p.text)
    return "".join(out)


def rec(name, ok, detail):
    RESULTS.append({"test": name, "passed": ok, "detail": detail})
    print(f"{'✅' if ok else '❌'} {name}: {detail}")


async def main():
    # A. SENSITIVE -> LLM 必須 0 次呼叫
    txt = await run("[SENSITIVE] 客戶身分證 A123456789，請摘要這筆資料。")
    rec("1_llm_never_called", CALLS["generate_content"] == 0,
        f"generate_content 呼叫 {CALLS['generate_content']} 次（需為 0）")
    rec("2_gate_triggered", COUNTERS["model_blocked"] == 1,
        f"model_blocked={COUNTERS['model_blocked']}")
    rec("3_blocked_in_output", "BLOCKED" in txt, f"output={txt[:80]!r}")

    # B. 對照組：一般內容應正常呼叫（證明 gate 不是無差別封鎖）
    await run("What is 2 + 2?")
    rec("4_normal_passes", CALLS["generate_content"] >= 1,
        f"generate_content 呼叫 {CALLS['generate_content']} 次（需 >=1）")

    pathlib.Path("evidence").mkdir(exist_ok=True)
    pathlib.Path("evidence/S2-results.json").write_text(
        json.dumps(RESULTS, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nGO" if all(r["passed"] for r in RESULTS) else "\nNO-GO")


asyncio.run(main())
PY

python tests/test_s2_egress_gate.py 2>&1 | tee evidence/S2-run.txt
```

---

## 通過標準

| # | 驗證 | 必須 |
|---|---|---|
| 1 | **`generate_content == 0`** | ★ 用計數器證明，不是看文字 |
| 2 | `model_blocked == 1` | gate 確實觸發 |
| 3 | 輸出含 BLOCKED | 使用者看得到明確拒絕 |
| 4 | **一般內容 `>= 1`** | ★ 對照組：證明不是無差別封鎖 |

> **第 4 項不能省。** 一個永遠拒絕的 gate 也會讓 1–3 全過，但它是壞掉的系統，不是安全的系統。**對照組是區分「安全」與「壞掉」的唯一方法。**

---

## 失敗處理

| 症狀 | 處置 |
|---|---|
| `CountingGemini` 無法繼承 | 改用 monkeypatch：`Gemini.generate_content_async` 包一層計數 |
| 計數 >0 但有 BLOCKED 文字 | **紅旗**：攔截發生在請求送出之後 → 這就是 fail-open，記錄後 NO-GO |
| callback 未觸發 | 確認 plugin 註冊在 `Runner(plugins=[...])` |

---

## 產出

```
tests/counting_model.py
tests/test_s2_egress_gate.py
evidence/S2-results.json
evidence/S2-run.txt
```

> 📝 **文章素材：** 「我怎麼知道資料真的沒送出去？」——回應文字不算證據，API 計數才算。這與你的 ControlEvidence 哲學同源：**主張需要證據支撐，不是宣稱。**
