"""Pydantic domain objects (S4). Shapes batch.py, evaluators.py, packet.py
agree on. hard_policy.py's ControlEvidence dicts predate this file and
follow the same shape by convention, not by importing it -- S1/S6 tests
assert on that exact dict, left unchanged.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

RiskTier = Literal["R0", "R1", "R2", "R3", "R4"]
Route = Literal["AUTO", "SAMPLE", "HUMAN_REVIEW", "BLOCK"]
EvalStatus = Literal["PASS", "FAIL", "WARN"]


class EvaluationResult(BaseModel):
    """Output of one pure-function evaluator (evaluators.py)."""
    evaluation: str
    score: float
    status: EvalStatus
    detail: str = ""


class RiskDecision(BaseModel):
    """Output of the risk router for one item: risk tier + route + why."""
    risk_tier: RiskTier
    route: Route
    policy_id: str
    reason: str


class ApprovalDecision(BaseModel):
    """A human reviewer's resolution of a HUMAN_REVIEW item (WS4-2)."""
    assessment_id: str
    decision: Literal["APPROVE", "REJECT"]
    reviewer: str
    created_at: str
    resolved_at: str | None = None


class Transformation(BaseModel):
    """v0.2 reserved: how content was transformed before release.
    v0.1 never transforms content -- type is always 'none'."""
    type: Literal["none"] = "none"
    reversible: bool | None = None
    note: str = "v0.1 synthetic data only"


class ControlEvidence(BaseModel):
    """The one artifact every batch item must produce, no exceptions."""
    control_id: str
    result: str
    detail: str
    trajectory: list[Any] = Field(default_factory=list)
    transformation: Transformation = Field(default_factory=Transformation)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())


def make_evidence(control_id: str, result: str, detail: str,
                   trajectory: list[Any]) -> ControlEvidence:
    """Per-item evidence constructor batch.py calls once per queue item."""
    return ControlEvidence(control_id=control_id, result=result,
                            detail=detail, trajectory=trajectory)
