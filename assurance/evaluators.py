"""Pure-function content evaluators. Zero LLM calls, zero side effects --
same input always produces the same EvaluationResult. Each wraps its
computation in evaluator_span() so the trajectory shows it actually ran.

Queue item shape (see data/make_queue.py):
{
  "id": str,
  "content": str,
  "data_class": "PUBLIC" | "INTERNAL" | "SENSITIVE",
  "claimed_sources": [url, ...],       # sources the content says it draws from
  "citations": [url, ...],             # sources actually cited in content
  "reference_date": "YYYY-MM-DD",      # frozen "as of" date, part of the input
  "source_fetched_at": {url: "YYYY-MM-DD", ...},
  "numeric_claims": [{"claim": str, "value": float, "source_value": float}],
}
"""
from __future__ import annotations
from datetime import date

from .schema import EvaluationResult
from .tracing import evaluator_span

SOURCE_TTL_DAYS = 90
NUMERIC_TOLERANCE = 0.01  # relative tolerance, e.g. 1%


def _record(name: str, score: float, status: str, detail: str) -> EvaluationResult:
    result = EvaluationResult(evaluation=name, score=score, status=status, detail=detail)
    with evaluator_span(f"eval.{name}", evaluation=name, score=score, status=status):
        pass
    return result


def citation_coverage(item: dict) -> EvaluationResult:
    claimed = set(item.get("claimed_sources") or [])
    cited = set(item.get("citations") or [])
    if not claimed:
        return _record("citation_coverage", 1.0, "PASS", "no sources claimed")
    covered = claimed & cited
    score = len(covered) / len(claimed)
    if score >= 0.8:
        status = "PASS"
    elif score >= 0.5:
        status = "WARN"
    else:
        status = "FAIL"
    missing = sorted(claimed - cited)
    return _record("citation_coverage", round(score, 3), status,
                    f"{len(covered)}/{len(claimed)} claimed sources cited; missing={missing}")


def content_integrity(item: dict) -> EvaluationResult:
    content = item.get("content") or ""
    if not content.strip():
        return _record("content_integrity", 0.0, "FAIL", "content is empty")
    if "[UNVERIFIED]" in content:
        return _record("content_integrity", 0.2, "FAIL",
                        "content contains [UNVERIFIED] marker")
    if "[DRAFT]" in content:
        return _record("content_integrity", 0.6, "WARN",
                        "content contains [DRAFT] marker")
    return _record("content_integrity", 1.0, "PASS", "no integrity markers found")


def source_ttl(item: dict) -> EvaluationResult:
    fetched_at = item.get("source_fetched_at") or {}
    ref = item.get("reference_date")
    if not fetched_at or not ref:
        return _record("source_ttl", 1.0, "PASS", "no sources to age-check")
    ref_date = date.fromisoformat(ref)
    ages = {url: (ref_date - date.fromisoformat(d)).days for url, d in fetched_at.items()}
    oldest_url, oldest_age = max(ages.items(), key=lambda kv: kv[1])
    if oldest_age > SOURCE_TTL_DAYS:
        return _record("source_ttl", 0.0, "FAIL",
                        f"{oldest_url} is {oldest_age}d old > TTL {SOURCE_TTL_DAYS}d")
    score = max(0.0, 1.0 - oldest_age / (SOURCE_TTL_DAYS * 2))
    status = "PASS" if oldest_age <= SOURCE_TTL_DAYS * 0.7 else "WARN"
    return _record("source_ttl", round(score, 3), status,
                    f"oldest source {oldest_url} is {oldest_age}d old (TTL {SOURCE_TTL_DAYS}d)")


def numeric_claim_check(item: dict) -> EvaluationResult:
    claims = item.get("numeric_claims") or []
    if not claims:
        return _record("numeric_claim_check", 1.0, "PASS", "no numeric claims")
    mismatches = []
    for c in claims:
        value, source_value = c["value"], c["source_value"]
        denom = abs(source_value) if source_value else 1.0
        rel_err = abs(value - source_value) / denom
        if rel_err > NUMERIC_TOLERANCE:
            mismatches.append(f"{c['claim']!r} claims {value} vs source {source_value}")
    if mismatches:
        return _record("numeric_claim_check", 0.0, "FAIL", "; ".join(mismatches))
    return _record("numeric_claim_check", 1.0, "PASS",
                    f"{len(claims)} numeric claim(s) match source within {NUMERIC_TOLERANCE:.0%}")


ALL_EVALUATORS = {
    "citation_coverage": citation_coverage,
    "content_integrity": content_integrity,
    "source_ttl": source_ttl,
    "numeric_claim_check": numeric_claim_check,
}
