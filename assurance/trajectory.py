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
