# S3 — 確定性流程與 Risk Router

**時間盒：** 60 分鐘
**GO/NO-GO：** 非決定項（有 fallback），但**發現的 fail-open 行為很重要**

---

## ⚠️ 查證修正：Python API 與 Go 文件範例不同

官方 route 文件範例是 **Go**。Python 的實際 API（已從 2.7.1 原始碼確認）：

| Go 文件 | **Python 實際** |
|---|---|
| `workflow.StringRoute("R3")` | `Edge(from_node=a, to_node=b, route="R3")` |
| `workflow.Default` | `DEFAULT_ROUTE`（常數 = `"__DEFAULT__"`） |
| `Event.Routes` | `Event(..., route="R3")` → `event.actions.route` |

```python
from google.adk.workflow import Workflow, Edge, FunctionNode, START, DEFAULT_ROUTE
```

---

## ★★★ 最重要的發現：未匹配 route 是 fail-open

`workflow/_graph.py:174-181` 原始碼：

```python
if has_routing_edges and not next_pending_nodes:
    logger.warning(
        "Node '%s' has conditional/DEFAULT edges but none were matched by the"
        " emitted route(s): %s. The branch will end.", ...)
```

**未匹配且無 DEFAULT edge → 只印一行 warning，branch 靜默結束。**

不拋例外、不走任何節點。

### 為什麼這對 assurance 系統是嚴重的

「什麼都沒發生」與「被明確擋下」在稽核上是**完全不同**的兩件事：

| | 結果 | ControlEvidence | 稽核時 |
|---|---|---|---|
| 靜默結束 | 無輸出 | **無** | 一片空白，無法證明任何事 |
| DEFAULT → HardBlock | BLOCKED | **有** | 可證明「政策判定並拒絕」 |

**所以 `DEFAULT_ROUTE → HardBlock` 不是加分項，是必要的安全網。**

這正是 Day 2 文章講的「保證 vs 運氣」在框架層的具體體現。

---

## 步驟 1：建立 Risk Router 圖（25 分）

```bash
cat > assurance/graph.py <<'PY'
"""確定性 Risk Router。路由決策 100% 由純 Python policy engine 產生。"""
from __future__ import annotations
from google.adk.workflow import Workflow, Edge, FunctionNode, START, DEFAULT_ROUTE
from google.adk.events import Event

TRACE: list[str] = []


def reset_trace() -> None:
    TRACE.clear()


# ---- 節點：每個都是純函式，零 LLM ----

def evidence(text: str) -> Event:
    TRACE.append("evidence")
    return Event(author="evidence", route=None)


def evaluate_node(ctx) -> Event:
    TRACE.append("evaluate")
    return Event(author="evaluate", route=None)


def risk_router(ctx) -> Event:
    """發出 route 值。此處為純 Python 判定，不涉及任何模型呼叫。"""
    TRACE.append("risk_router")
    tier = ctx.session.state.get("risk_tier", "R4") if hasattr(ctx, "session") else "R4"
    return Event(author="risk_router", route=tier)


def auto(ctx) -> Event:
    TRACE.append("auto"); return Event(author="auto")


def sample(ctx) -> Event:
    TRACE.append("sample"); return Event(author="sample")


def human_approval(ctx) -> Event:
    TRACE.append("human_approval"); return Event(author="human_approval")


def hard_block(ctx) -> Event:
    TRACE.append("hard_block"); return Event(author="hard_block")


def build_workflow() -> Workflow:
    n_ev = FunctionNode(func=evidence, name="evidence")
    n_eval = FunctionNode(func=evaluate_node, name="evaluate")
    n_rr = FunctionNode(func=risk_router, name="risk_router")
    n_auto = FunctionNode(func=auto, name="auto")
    n_smp = FunctionNode(func=sample, name="sample")
    n_hum = FunctionNode(func=human_approval, name="human_approval")
    n_blk = FunctionNode(func=hard_block, name="hard_block")

    return Workflow(
        name="risk_router_wf",
        edges=[
            Edge(from_node=START,  to_node=n_ev),
            Edge(from_node=n_ev,   to_node=n_eval),
            Edge(from_node=n_eval, to_node=n_rr),
            # 條件路由
            Edge(from_node=n_rr, to_node=n_auto, route=["R0", "R1"]),
            Edge(from_node=n_rr, to_node=n_smp,  route="R2"),
            Edge(from_node=n_rr, to_node=n_hum,  route="R3"),
            Edge(from_node=n_rr, to_node=n_blk,  route="R4"),
            # ★ 安全網：任何未匹配的 route 落到 HardBlock
            Edge(from_node=n_rr, to_node=n_blk,  route=DEFAULT_ROUTE),
        ],
    )
PY
echo "✅ assurance/graph.py"
```

---

## 步驟 2：驗證確定性與 fail-closed 拓撲（25 分）

```bash
cat > tests/test_s3_routing.py <<'PY'
"""S3: 路由確定性 + DEFAULT_ROUTE 安全網 + 無 LLM 參與。"""
import json, pathlib, inspect
from google.adk.workflow import DEFAULT_ROUTE
from google.adk.workflow._graph import Graph
from assurance import graph as G

RESULTS = []
def rec(n, ok, d):
    RESULTS.append({"test": n, "passed": ok, "detail": d})
    print(f"{'✅' if ok else '❌'} {n}: {d}")


wf = G.build_workflow()
edges = wf.graph.edges if hasattr(wf, "graph") else wf.edges
nodes = {}
for e in edges:
    nodes[e.from_node.name] = e.from_node
    nodes[e.to_node.name] = e.to_node
g = Graph(nodes=list(nodes.values()), edges=list(edges))

# --- 1. 各風險等級路由正確 ---
expect = {"R0": "auto", "R1": "auto", "R2": "sample",
          "R3": "human_approval", "R4": "hard_block"}
for tier, want in expect.items():
    got = g.get_next_pending_nodes("risk_router", tier)
    rec(f"1_route_{tier}", got == [want], f"{tier} -> {got} (需 ['{want}'])")

# --- 2. ★ 未知 route 落到 DEFAULT -> hard_block ---
for bad in ["R99", "UNKNOWN", "", "R"]:
    got = g.get_next_pending_nodes("risk_router", bad)
    rec(f"2_default_{bad or 'empty'}", got == ["hard_block"],
        f"route={bad!r} -> {got} (需 ['hard_block'])")

got_none = g.get_next_pending_nodes("risk_router", None)
rec("2_default_None", got_none == ["hard_block"], f"route=None -> {got_none}")

# --- 3. 確定性：同輸入跑 10 次結果一致 ---
runs = [g.get_next_pending_nodes("risk_router", "R3") for _ in range(10)]
rec("3_deterministic", all(r == runs[0] for r in runs),
    f"10 次結果一致: {runs[0]}")

# --- 4. router 節點不含任何 LLM 呼叫 ---
src = inspect.getsource(G.risk_router)
banned = ["generate_content", "LlmAgent", "model", "genai"]
found = [b for b in banned if b in src]
rec("4_no_llm_in_router", not found,
    f"risk_router 原始碼未含 {banned}；發現={found}")

# --- 5. ★ 證明「沒有 DEFAULT edge 時會 fail-open」---
edges_no_default = [e for e in edges if e.route != DEFAULT_ROUTE]
g2 = Graph(nodes=list(nodes.values()), edges=edges_no_default)
leaked = g2.get_next_pending_nodes("risk_router", "R99")
rec("5_fail_open_without_default", leaked == [],
    f"移除 DEFAULT edge 後 route=R99 -> {leaked} "
    f"(空 list = 靜默結束 = fail-open，這正是要防的)")

pathlib.Path("evidence").mkdir(exist_ok=True)
pathlib.Path("evidence/S3-results.json").write_text(
    json.dumps(RESULTS, indent=2, ensure_ascii=False), encoding="utf-8")
print("\nPASS" if all(r["passed"] for r in RESULTS) else "\nFAIL")
PY

python tests/test_s3_routing.py 2>&1 | tee evidence/S3-run.txt
```

---

## 通過標準

| # | 驗證 | 必須 |
|---|---|---|
| 1 | R0–R4 各自路由正確 | 5/5 |
| 2 | 未知 route → `hard_block` | 含 `None`、空字串 |
| 3 | 10 次結果一致 | 確定性 |
| 4 | router 原始碼無 LLM 呼叫 | 純 Python 判定 |
| 5 | **移除 DEFAULT edge → 回傳空 list** | ★ 證明 fail-open 風險真實存在 |

**第 5 項是這個 spike 最有價值的產出。** 它不是在測你的程式碼，是在**證明框架的預設行為是不安全的**，而你的設計修正了它。

---

## 失敗處理

| 症狀 | 處置 |
|---|---|
| `Event(route=...)` 報錯 | 改用 `Event(author=..., actions=EventActions(route="R3"))` |
| `wf.graph` 不存在 | 直接用建構時的 edges list 建 `Graph` |
| FunctionNode 簽章不符 | `inspect.signature(FunctionNode.__init__)` 查實際參數 |
| Graph API 大改 | **fallback：** 用 `SequentialAgent` + 自製 `BaseAgent` 路由（S0 已確認未 deprecated），成本 +3 小時，仍 GO |

---

## 產出

```
assurance/graph.py
tests/test_s3_routing.py
evidence/S3-results.json
evidence/S3-run.txt
```

> 📝 **文章素材（強）：** 「我的 fail-closed 設計，差點被框架的預設 fail-open 行為破壞」。
> 圖的形狀就是政策——`DEFAULT_ROUTE → HardBlock` 讓「未知風險等級不會靜默通過」變成**拓撲保證**，而不是程式碼裡一行 `else`。
