"""所有 policy id 的單一來源。禁止在別處硬編碼字串。"""
from __future__ import annotations
from typing import NamedTuple


class Policy(NamedTuple):
    id: str
    owner: str        # 哪個 plugin 負責執行
    description: str


ALLOW_REGISTERED   = Policy("FIN-AI-000", "HardPolicyPlugin", "Registered PUBLIC source")
UNKNOWN_SOURCE     = Policy("FIN-AI-001", "HardPolicyPlugin", "Unregistered source -> fail closed")
INTERNAL_NO_EGRESS = Policy("FIN-AI-002", "HardPolicyPlugin", "INTERNAL data must not reach external tools")
SENSITIVE_NO_MODEL = Policy("FIN-AI-003", "EgressGatePlugin", "Sensitive content must not reach external model")
R4_PROHIBITED      = Policy("FIN-AI-004", "HardPolicyGate",   "PROHIBITED: no human override")

# ---- batch content-risk router (WS2): routes queue items to AUTO / SAMPLE /
# HUMAN_REVIEW / BLOCK based on evaluator results + data_class. Distinct
# scope from FIN-AI-000..004 above (source registry / egress / override). ----
EVALUATOR_FAIL     = Policy("FIN-AI-005", "release_router", "Evaluator FAIL -> block release")
UNKNOWN_DATA_CLASS = Policy("FIN-AI-006", "release_router", "Unknown data_class -> fail closed BLOCK")
SENSITIVE_FLOOR    = Policy("FIN-AI-007", "release_router", "SENSITIVE content floors to human review")
EVALUATOR_WARN     = Policy("FIN-AI-008", "release_router", "Evaluator WARN -> human review")
LOW_CONFIDENCE     = Policy("FIN-AI-009", "release_router", "Low-confidence PASS -> sampled for review")
CLEAN_AUTO         = Policy("FIN-AI-010", "release_router", "All evaluators PASS, high confidence -> auto release")

# ---- data sovereignty (WS4-3): distinct from FIN-AI-003 (keyword-marker
# egress gate) -- this is a data_class-based pre-check. ----
SOVEREIGNTY_BLOCK  = Policy("FIN-AI-011", "SovereigntyGatePlugin", "SENSITIVE/unknown data_class must not egress externally")

ALL = [ALLOW_REGISTERED, UNKNOWN_SOURCE, INTERNAL_NO_EGRESS,
       SENSITIVE_NO_MODEL, R4_PROHIBITED,
       EVALUATOR_FAIL, UNKNOWN_DATA_CLASS, SENSITIVE_FLOOR,
       EVALUATOR_WARN, LOW_CONFIDENCE, CLEAN_AUTO,
       SOVEREIGNTY_BLOCK]
BY_ID = {p.id: p for p in ALL}
