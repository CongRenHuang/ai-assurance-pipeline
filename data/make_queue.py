"""Generates the synthetic 100-item queue used by assurance.batch (WS2-3).

Fixed seed for reproducibility. A handful of items per risk tier are
deliberately planted (R2/R3/R4) so the pipeline is known to exercise every
route at least once; everything else is randomized and falls where the
rules put it -- counts are not tuned to hit a target ratio.

Run: python data/make_queue.py > data/queue.jsonl
"""
from __future__ import annotations
import json
import random
import sys
from datetime import date, timedelta

SEED = 42
N_ITEMS = 100
REFERENCE_DATE = date(2026, 8, 31)  # frozen "as of" date, part of every item

SOURCES = [
    "https://example.com/report-a",
    "https://example.com/report-b",
    "https://example.com/filing-c",
    "https://example.com/press-d",
]

TOPICS = [
    "Q3 earnings summary", "annual risk disclosure", "product launch brief",
    "regulatory filing digest", "market outlook memo", "vendor audit note",
    "customer incident report", "compliance training summary",
]


def _iso(d: date) -> str:
    return d.isoformat()


def _fresh_sources(rng: random.Random, urls: list[str], max_age_days: int) -> dict[str, str]:
    return {u: _iso(REFERENCE_DATE - timedelta(days=rng.randint(0, max_age_days))) for u in urls}


def _base_item(item_id: str, rng: random.Random) -> dict:
    n_sources = rng.randint(1, 3)
    claimed = rng.sample(SOURCES, n_sources)
    return {
        "id": item_id,
        "content": f"{rng.choice(TOPICS)} drafted from {n_sources} source(s).",
        "data_class": "PUBLIC",
        "claimed_sources": claimed,
        "citations": list(claimed),
        "reference_date": _iso(REFERENCE_DATE),
        "source_fetched_at": _fresh_sources(rng, claimed, max_age_days=30),
        "numeric_claims": [],
    }


def make_r4_item(item_id: str, rng: random.Random, variant: int) -> dict:
    """Deliberately FAIL an evaluator -> R4/BLOCK."""
    item = _base_item(item_id, rng)
    if variant == 0:
        item["content"] = ""  # content_integrity FAIL: empty
    elif variant == 1:
        item["content"] += " [UNVERIFIED]"  # content_integrity FAIL
    elif variant == 2:
        item["citations"] = []  # citation_coverage FAIL: nothing cited
    else:
        item["numeric_claims"] = [
            {"claim": "revenue grew 12%", "value": 12.0, "source_value": 4.0}
        ]  # numeric_claim_check FAIL
    return item


def make_r3_item(item_id: str, rng: random.Random, variant: int) -> dict:
    """Deliberately land in HUMAN_REVIEW via SENSITIVE data_class or a WARN."""
    item = _base_item(item_id, rng)
    if variant == 0:
        item["data_class"] = "SENSITIVE"
    else:
        item["content"] += " [DRAFT]"  # content_integrity WARN
    return item


def make_r2_item(item_id: str, rng: random.Random) -> dict:
    """All PASS but low-confidence (aged source) -> SAMPLE."""
    item = _base_item(item_id, rng)
    item["source_fetched_at"] = _fresh_sources(rng, item["claimed_sources"], max_age_days=63)
    for url in item["source_fetched_at"]:
        item["source_fetched_at"][url] = _iso(REFERENCE_DATE - timedelta(days=rng.randint(40, 62)))
    return item


def make_random_item(item_id: str, rng: random.Random) -> dict:
    """Not steered toward any tier -- rules decide where it lands."""
    item = _base_item(item_id, rng)
    item["source_fetched_at"] = _fresh_sources(rng, item["claimed_sources"], max_age_days=55)
    if rng.random() < 0.15:
        item["citations"] = rng.sample(item["claimed_sources"],
                                        k=max(0, len(item["claimed_sources"]) - 1))
    if rng.random() < 0.2:
        item["numeric_claims"] = [
            {"claim": "quarterly growth", "value": v, "source_value": v}
            for v in [round(rng.uniform(1, 20), 1)]
        ]
    if rng.random() < 0.05:
        item["data_class"] = "INTERNAL"
    return item


def build_queue() -> list[dict]:
    rng = random.Random(SEED)
    items: list[dict] = []

    for i in range(5):
        items.append(make_r4_item(f"ASMT-{len(items) + 1:03d}", rng, i % 4))
    for i in range(5):
        items.append(make_r3_item(f"ASMT-{len(items) + 1:03d}", rng, i % 2))
    for _ in range(5):
        items.append(make_r2_item(f"ASMT-{len(items) + 1:03d}", rng))

    while len(items) < N_ITEMS:
        items.append(make_random_item(f"ASMT-{len(items) + 1:03d}", rng))

    rng.shuffle(items)
    # re-sequence ids after shuffle so ASMT-NNN stays a stable, ordered key
    for i, item in enumerate(items, start=1):
        item["id"] = f"ASMT-{i:03d}"
    return items


def main() -> None:
    for item in build_queue():
        sys.stdout.write(json.dumps(item, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
