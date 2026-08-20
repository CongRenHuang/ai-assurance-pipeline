# S9 ★ — Trajectory Assertion（執行軌跡斷言）

**時間盒：** 60 分鐘
**前置：** S7 必須先完成（trajectory 從 span tree 抽取）
**GO/NO-GO：** 非決定項，但**這是把 S1/S2/S6 從「測試通過」升級為「可稽核保證」的關鍵一步**

---

## 核心命題

> **最終結果正確，不代表 agent 行為正確。**

你已經在 S8 親身踩到這件事：R4 被擋了、測試會過、demo 看起來完美——但擋它的是 `HardPolicyPlugin` 的來源誤判，不是 `HardPolicyGate` 的 R4 政策。

**正確結果 + 錯誤原因 = 仍然是 bug。**

S9 要做的，就是讓這件事**在測試層面不可能再隱形**。

---

## 設計原則：約束 invariant，不約束 path

不要斷言「實際路徑 == 黃金路徑」——完整 path coverage 在組合上就是爆炸的，做不到，而且會消滅 agent 應有的自主性。

要斷言的是**性質**：

| 類型 | 你的案例 |
|---|---|
| **禁止轉移** | 外部模型呼叫的前驅，不得是未解析的 UNKNOWN 來源 |
| **必要前驅** | 任何 `Approve` 之前，必須經過 hard policy 檢查 |
| **副作用基數** | 單次 assessment 的外送次數 ≤ 政策允許值 |
| **強制檢查點** | R3 路徑必含 ApprovalDecision；R4 必含 HardBlock |
| **★ 歸因正確** | **R4 的 BLOCK 必須由 `HardPolicyGate` 做出，不是被前面的 plugin 誤擋** |

最後一項是這次 bug 的 regression test。**沒有它，你的 R4 保證仍然只是「看起來對」。**

> 自主性活在 invariant 之間的空隙裡。這和型別系統不消滅程式設計自由是同一個道理：**它約束非法，不規定合法。**

---

## 步驟 1：從 span tree 抽 trajectory（20 分）

```bash
cat > assurance/trajectory.py <<'PY'
"""從 OpenInference span tree 抽取執行軌跡，並提供 invariant 斷言。

為什麼從 span 抽而不是手動記錄：
手動 append 的 trajectory 是「程式宣稱它做了什麼」，
span tree 是「執行期實際發生了什麼」。後者才是證據。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterable

SPAN_KIND = "openinference.span.kind"


@dataclass
class Step:
    """軌跡中的一步。"""
    name: str
    kind: str                      # GUARDRAIL / EVALUATOR / LLM / TOOL / CHAIN
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def policy_id(self) -> str | None:
        return self.attributes.get("assurance.policy_id")

    @property
    def plugin(self) -> str | None:
        return self.attributes.get("assurance.plugin")

    @property
    def decision(self) -> str | None:
        return self.attributes.get("assurance.decision")

    def __repr__(self) -> str:
        extra = f"/{self.plugin}" if self.plugin else ""
        return f"{self.name}[{self.kind}{extra}]"


@dataclass
class Trajectory:
    """一次執行的完整軌跡。"""
    steps: list[Step] = field(default_factory=list)

    # ---------- 建構 ----------
    @classmethod
    def from_spans(cls, spans: Iterable[dict]) -> "Trajectory":
        """從 CapturingExporter 的 span dict 建構。

        依 start_time 排序；若無則保留匯出順序（SimpleSpanProcessor 為
        結束順序，子 span 先於父 span）。
        """
        items = list(spans)
        if items and items[0].get("start_time") is not None:
            items.sort(key=lambda s: s.get("start_time") or 0)
        return cls(steps=[
            Step(name=s["name"],
                 kind=(s.get("attributes") or {}).get(SPAN_KIND, "UNKNOWN"),
                 attributes=dict(s.get("attributes") or {}))
            for s in items
        ])

    # ---------- 查詢 ----------
    @property
    def names(self) -> list[str]:
        return [s.name for s in self.steps]

    def of_kind(self, kind: str) -> list[Step]:
        return [s for s in self.steps if s.kind == kind]

    def index_of(self, name: str) -> int:
        for i, s in enumerate(self.steps):
            if s.name == name:
                return i
        return -1

    # ---------- Invariant 斷言 ----------
    def assert_required_predecessor(self, target: str, predecessor: str) -> None:
        """必要前驅：target 出現時，predecessor 必須更早出現。"""
        ti = self.index_of(target)
        if ti < 0:
            return                                    # target 未發生，無需檢查
        pi = self.index_of(predecessor)
        assert 0 <= pi < ti, (
            f"必要前驅違反：'{target}' 之前找不到 '{predecessor}'。"
            f" 實際軌跡={self.names}")

    def assert_forbidden_transition(self, frm: str, to: str) -> None:
        """禁止轉移：frm 不得直接接到 to。"""
        for a, b in zip(self.steps, self.steps[1:]):
            assert not (a.name == frm and b.name == to), (
                f"禁止轉移違反：'{frm}' -> '{to}'。實際軌跡={self.names}")

    def assert_side_effect_cardinality(self, name: str, max_times: int) -> None:
        """副作用基數：某步驟最多出現幾次。"""
        n = sum(1 for s in self.steps if s.name == name)
        assert n <= max_times, (
            f"副作用基數違反：'{name}' 出現 {n} 次 > 上限 {max_times}。"
            f" 實際軌跡={self.names}")

    def assert_mandatory_checkpoint(self, name: str) -> None:
        """強制檢查點：必須出現。"""
        assert self.index_of(name) >= 0, (
            f"強制檢查點缺失：'{name}' 未出現。實際軌跡={self.names}")

    def assert_decided_by(self, policy_id: str, plugin: str) -> None:
        """★ 歸因正確：某政策的決定必須由指定 plugin 做出。

        這是 cross-plugin false-block bug 的 regression 斷言：
        正確結果 + 錯誤原因 = 仍然是 bug。
        """
        hits = [s for s in self.steps if s.policy_id == policy_id]
        assert hits, (
            f"歸因失敗：軌跡中找不到 policy_id='{policy_id}'。"
            f" 實際 policy_ids="
            f"{[s.policy_id for s in self.steps if s.policy_id]}")
        actual = {s.plugin for s in hits}
        assert actual == {plugin}, (
            f"歸因錯誤：policy_id='{policy_id}' 應由 '{plugin}' 決定，"
            f" 實際為 {actual}。這正是『正確結果、錯誤原因』。")

    # ---------- 匯出 ----------
    def to_evidence(self) -> list[dict[str, Any]]:
        """轉為 ControlEvidence.trajectory 欄位。"""
        out = []
        for s in self.steps:
            item = {"step": s.name, "kind": s.kind}
            if s.policy_id: item["policy_id"] = s.policy_id
            if s.plugin:    item["plugin"] = s.plugin
            if s.decision:  item["decision"] = s.decision
            out.append(item)
        return out
PY
echo "OK assurance/trajectory.py"
```

---

## 步驟 2：對照測試（25 分）

**兩個測試是一組。單獨看第一個會產生「有檢查就安全」的錯覺。**

```bash
cat > tests/test_s9_trajectory.py <<'PY'
"""S9: trajectory invariant 斷言。

核心對照：兩條路徑最終狀態都是 BLOCKED，
只有一條是保證，另一條是運氣（或錯誤歸因）。
"""
import json, pathlib, sys

from assurance.trajectory import Trajectory, Step

RESULTS = []


def rec(name, passed, detail):
    RESULTS.append({"test": name, "passed": passed, "detail": detail})
    print(f"{'PASS' if passed else 'FAIL'} {name}: {detail}")


def expect_ok(name, fn, detail=""):
    try:
        fn(); rec(name, True, detail or "invariant 成立")
    except AssertionError as e:
        rec(name, False, str(e)[:200])


def expect_raises(name, fn, detail=""):
    try:
        fn(); rec(name, False, "應該要拋 AssertionError 但沒有")
    except AssertionError:
        rec(name, True, detail or "正確地偵測到違反")


# ============ 情境 A：政策路徑（保證）============
GOOD = Trajectory(steps=[
    Step("release_assessment", "CHAIN"),
    Step("eval.citation_coverage", "EVALUATOR",
         {"assurance.evaluation": "citation_coverage"}),
    Step("policy.hard_block", "GUARDRAIL", {
        "assurance.policy_id": "FIN-AI-004",
        "assurance.plugin": "HardPolicyGate",
        "assurance.decision": "BLOCK",
        "assurance.override_rejected": True,
    }),
])

# ============ 情境 B：錯誤歸因（S8 真實 bug）============
# 最終也是 BLOCKED，但擋它的是來源治理誤判，R4 檢查從未執行
MISATTRIBUTED = Trajectory(steps=[
    Step("release_assessment", "CHAIN"),
    Step("policy.source_governance", "GUARDRAIL", {
        "assurance.policy_id": "FIN-AI-001",
        "assurance.plugin": "HardPolicyPlugin",
        "assurance.decision": "BLOCK",
    }),
])

# ============ 情境 C：運氣路徑 ============
LUCKY = Trajectory(steps=[Step("release_assessment", "CHAIN")])


print("\n--- 1. 強制檢查點 ---")
expect_ok("1a_good_has_checkpoint",
          lambda: GOOD.assert_mandatory_checkpoint("policy.hard_block"))
expect_raises("1b_lucky_missing_checkpoint",
              lambda: LUCKY.assert_mandatory_checkpoint("policy.hard_block"),
              "運氣路徑沒有經過 hard_block -> 正確判 FAIL")

print("\n--- 2. 歸因正確（S8 bug 的 regression）---")
expect_ok("2a_good_attribution",
          lambda: GOOD.assert_decided_by("FIN-AI-004", "HardPolicyGate"))
expect_raises("2b_misattributed_detected",
              lambda: MISATTRIBUTED.assert_decided_by("FIN-AI-004", "HardPolicyGate"),
              "R4 未被 HardPolicyGate 決定 -> 正確判 FAIL")

print("\n--- 3. 必要前驅 ---")
APPROVED = Trajectory(steps=[
    Step("policy.hard_policy_check", "GUARDRAIL",
         {"assurance.policy_id": "FIN-AI-004", "assurance.plugin": "HardPolicyGate"}),
    Step("approve", "TOOL"),
])
BAD_APPROVE = Trajectory(steps=[Step("approve", "TOOL")])
expect_ok("3a_approve_after_check",
          lambda: APPROVED.assert_required_predecessor("approve", "policy.hard_policy_check"))
expect_raises("3b_approve_without_check",
              lambda: BAD_APPROVE.assert_required_predecessor("approve", "policy.hard_policy_check"),
              "核准前未經 hard policy 檢查 -> 正確判 FAIL")

print("\n--- 4. 副作用基數 ---")
DOUBLE = Trajectory(steps=[Step("external_model_call", "LLM"),
                           Step("external_model_call", "LLM")])
expect_ok("4a_within_limit",
          lambda: GOOD.assert_side_effect_cardinality("external_model_call", 1))
expect_raises("4b_exceeds_limit",
              lambda: DOUBLE.assert_side_effect_cardinality("external_model_call", 1),
              "外送 2 次 > 上限 1 -> 正確判 FAIL")

print("\n--- 5. 禁止轉移 ---")
UNSAFE = Trajectory(steps=[Step("unknown_source", "GUARDRAIL"),
                           Step("external_model_call", "LLM")])
expect_ok("5a_no_forbidden",
          lambda: GOOD.assert_forbidden_transition("unknown_source", "external_model_call"))
expect_raises("5b_forbidden_detected",
              lambda: UNSAFE.assert_forbidden_transition("unknown_source", "external_model_call"),
              "UNKNOWN 來源直接接外部模型 -> 正確判 FAIL")

print("\n--- 6. 只看結果 vs 看軌跡 ---")
result_only = all(t.index_of("release_assessment") >= 0
                  for t in (GOOD, MISATTRIBUTED, LUCKY))
rec("6a_result_only_all_pass", result_only,
    "只斷言最終狀態 -> 三條路徑全部 PASS（問題所在）")

def traj_check(t):
    try:
        t.assert_decided_by("FIN-AI-004", "HardPolicyGate"); return True
    except AssertionError:
        return False

survivors = [n for n, t in
             (("GOOD", GOOD), ("MISATTRIBUTED", MISATTRIBUTED), ("LUCKY", LUCKY))
             if traj_check(t)]
rec("6b_trajectory_only_good_passes", survivors == ["GOOD"],
    f"看軌跡 -> 只有 {survivors} 通過")

print("\n" + "=" * 64)
print("  三條路徑最終狀態都是 BLOCKED。")
print("  只斷言 result 的測試：三條全 PASS。")
print("  斷言 trajectory 的測試：只有 GOOD 通過。")
print("=" * 64)

pathlib.Path("evidence").mkdir(exist_ok=True)
pathlib.Path("evidence/S9-results.json").write_text(
    json.dumps({"results": RESULTS,
                "good_trajectory": GOOD.to_evidence(),
                "misattributed_trajectory": MISATTRIBUTED.to_evidence()},
               indent=2, ensure_ascii=False), encoding="utf-8")

ok = all(r["passed"] for r in RESULTS)
print("\n" + ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
PY
PYTHONPATH=. uv run python tests/test_s9_trajectory.py 2>&1 | tee evidence/S9-run.txt
```

---

## 步驟 3：接上真實 span（15 分）

```bash
cat > tests/test_s9_from_real_spans.py <<'PY'
"""S9: 從 S7 的真實 span tree 抽 trajectory，而非手工構造。"""
import json, pathlib
from assurance import tracing as T
from assurance.trajectory import Trajectory

T.setup(use_otlp=False)
T.CAPTURED.clear()

with T.tracer().start_as_current_span("release_assessment") as root:
    root.set_attribute(T.SPAN_KIND, T.CHAIN)
    with T.evaluator_span("eval.citation_coverage",
                          evaluation="citation_coverage",
                          score=0.96, status="PASS"):
        pass
    with T.guardrail_span("policy.hard_block",
                          policy_id="FIN-AI-004", risk_tier="R4",
                          decision="BLOCK", override_rejected=True,
                          plugin="HardPolicyGate"):
        pass

T._provider.force_flush()

traj = Trajectory.from_spans(T.CAPTURED)
print("抽出的軌跡：", traj.names)

traj.assert_mandatory_checkpoint("policy.hard_block")
traj.assert_decided_by("FIN-AI-004", "HardPolicyGate")
print("invariant 全部成立")

pathlib.Path("evidence/S9-real-spans.json").write_text(
    json.dumps(traj.to_evidence(), indent=2, ensure_ascii=False), encoding="utf-8")
print("-> evidence/S9-real-spans.json")
PY
PYTHONPATH=. uv run python tests/test_s9_from_real_spans.py 2>&1 | tee -a evidence/S9-run.txt
```

> ⚠️ 這一步需要 S7 的 `guardrail_span` 支援 `plugin=` 參數（見 S7-REVIEW）。若 S7 尚未加，先跳過步驟 3。

---

## 通過標準

| # | 驗證 | 必須 |
|---|---|---|
| 1a/1b | 強制檢查點：好的過、運氣的 FAIL | 對照組 |
| **2a/2b** | **歸因正確：誤歸因被偵測** | ★ S8 bug 的 regression |
| 3a/3b | 必要前驅：未經檢查的核准被擋 | 對照組 |
| 4a/4b | 副作用基數 | 對照組 |
| 5a/5b | 禁止轉移 | 對照組 |
| **6b** | **只有 GOOD 通過軌跡檢查** | ★ 靈魂 |

**每一項都是「一個該過、一個該擋」的對照組。** 只驗證正向案例的測試無法區分「安全」與「壞掉」。

---

## 失敗處理

| 症狀 | 處置 |
|---|---|
| span 順序不對 | `CapturingExporter` 加記 `start_time`；`from_spans` 已支援排序 |
| `assurance.plugin` 不存在 | 先做 S7-REVIEW 的修正 |
| span 抽不出 trajectory | 退回 `hard_policy.py` 既有的手動 `_emit` trajectory，成本 +1h |

---

## 產出

```
assurance/trajectory.py
tests/test_s9_trajectory.py
tests/test_s9_from_real_spans.py
evidence/S9-results.json
evidence/S9-real-spans.json
evidence/S9-run.txt
```

**接上 ControlEvidence：**

```python
evidence.trajectory = traj.to_evidence()
```

至此 `ControlEvidence` 同時具備：**結論**（result）、**依據**（policy_id）、**歸因**（plugin）、**路徑**（trajectory）、**資料處理狀態**（transformation）。這就是「可辯護的決策」的完整形狀。
