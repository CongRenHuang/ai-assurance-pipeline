# 執行前必讀：三處與原 checklist 不同的查證修正

**查證方式：** 直接解開 `google_adk-2.7.1-py3-none-any.whl` 讀原始碼，非依賴文件描述。
**環境：** ADK 2.7.1（2026-08-17 發布）、Python 3.14（官方 classifier 支援）。

---

## 修正 1 ★★★ 「陷阱 0」在 Plugin 層**不成立**，在 Agent 層**成立**

原 checklist 說「回傳空 dict `{}` 是 falsy，不會攔截」。實測原始碼後，這句話**只對一半**：

### Plugin 層 → `is not None`（空 dict **會**擋）

`plugins/plugin_manager.py:307`

```python
if result is not None:
    logger.info("Plugin '%s' returned a value for callback '%s', exiting early.")
    return result
```

### Agent 層 → truthy（空 dict **不會**擋）

`flows/llm_flows/functions.py:621`

```python
if function_response:   # ← truthy 判定，{} 會通過
```

### 這對你的設計意味著什麼

| | 判定 | 空 dict 行為 |
|---|---|---|
| **Plugin** `before_tool_callback` | `is not None` | ✅ 擋下 |
| **Agent** `before_tool_callback` | truthy | ❌ 放行 |

**結論：把 hard policy 放在 Plugin 層不只是「不可繞過」，也剛好避開了 truthy 陷阱。** 這強化了原本的架構決策，但**理由和原本想的不一樣**——值得寫進文章。

S1 仍要實測這兩層的差異，那是你的一手證據。

---

## 修正 2 ★★★ Graph 的「未匹配 route」預設是 **fail-open**

`workflow/_graph.py:174-181`：

```python
if has_routing_edges and not next_pending_nodes:
    logger.warning(
        "Node '%s' has conditional/DEFAULT edges but none were matched by the"
        " emitted route(s): %s. The branch will end.", ...)
```

**未匹配且沒有 DEFAULT edge → 只印一行 warning，branch 靜默結束。**

不會拋例外、不會走向任何節點。對 assurance 系統來說，「什麼都沒發生」跟「被明確擋下」是**完全不同**的兩件事——前者沒有 ControlEvidence，稽核時等於空白。

**因此 `DEFAULT_ROUTE → HardBlock` 不是「加分項」，是必要的安全網。** S3 必須實測這個行為。

---

## 修正 3 Python API 與 Go 範例不同（原 checklist 已警告，此處給出正確形式）

| Go 文件範例 | **Python 實際 API** |
|---|---|
| `workflow.StringRoute("R3")` | `Edge(from_node=..., to_node=..., route="R3")` |
| `workflow.Default` | `DEFAULT_ROUTE`（常數，值為 `"__DEFAULT__"`） |
| `Event.Routes` | `Event(..., route="R3")` → 存入 `event.actions.route` |

正確 import：

```python
from google.adk.workflow import Workflow, Edge, FunctionNode, START, DEFAULT_ROUTE
```

`route` 欄位型別：`RouteValue | list[RouteValue] | None`
- `None` → 無條件邊，永遠觸發
- 單值或 list → list 表示「任一匹配即觸發」

---

## 其他已驗證的 API 細節

**Plugin callback 是 keyword-only，參數名必須完全正確：**

```python
async def before_tool_callback(
    self, *, tool: BaseTool, tool_args: dict[str, Any], tool_context: ToolContext
) -> Optional[dict]:
```

注意是 **`tool_args`** 不是 `args`。寫錯會 TypeError。

**FunctionTool confirmation：**

```python
FunctionTool(func, require_confirmation=True)          # bool
FunctionTool(func, require_confirmation=callable)      # 動態，可 async
```
`function_tool.py:300` → `return bool(self._require_confirmation)`

---

## 執行順序與時間盒

```
S0 (30m) → S1 ★ (60m) → S2 ★ (30m) → S3 (60m)
                ↓
        S1 失敗 → 直接 NO-GO，不要繼續

S4 (60m) → S5 (90m) → S6 ★ (45m) → S7 (45m) → S8 (60m)
```

**GO 條件：S1 + S2 + S6 全過。**
其餘失敗都有 workaround，加總 ≤ 8 小時仍 GO。

---

## 專案結構（S0 建立，後續共用）

```
Project/
├── .venv/
├── .env                      # GOOGLE_API_KEY（勿進版控）
├── .gitignore
├── assurance/
│   ├── __init__.py
│   ├── policy.py             # S1: 純函式 policy engine
│   ├── plugin.py             # S1/S2: HardPolicyPlugin
│   ├── schema.py             # S4: Pydantic domain objects
│   └── trajectory.py         # S9
├── spike_agent/
│   ├── __init__.py
│   └── agent.py              # root_agent（adk web / deploy 進入點）
├── tests/
└── evidence/                 # 每個 spike 的輸出證據
```
