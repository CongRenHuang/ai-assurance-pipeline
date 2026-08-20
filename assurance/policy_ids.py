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

ALL = [ALLOW_REGISTERED, UNKNOWN_SOURCE, INTERNAL_NO_EGRESS,
       SENSITIVE_NO_MODEL, R4_PROHIBITED]
BY_ID = {p.id: p for p in ALL}
