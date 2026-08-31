#!/usr/bin/env python
"""WS4-1: generates public/.well-known/agent.json from policy_ids.py.

Never hand-edit the JSON -- the `enforces` list must always equal
policy_ids.ALL's ids exactly, and this script is what keeps that true.

    python scripts/gen_agent_card.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from assurance import policy_ids as pid
from assurance.hard_policy import PROHIBITED
from assurance.sovereignty import ALLOWED_REGION, DOMAIN_POLICY

OUT_PATH = Path(__file__).resolve().parent.parent / "public" / ".well-known" / "agent.json"


def build_card() -> dict:
    # R4 is the only policy hard_policy.py's PROHIBITED dict marks as
    # override-proof -- pull that from the source of truth, don't restate it.
    not_overridable = [pid.R4_PROHIBITED.id] if "R4" in PROHIBITED else []

    return {
        "purpose": (
            "Release Assessment Agent: turns AI evidence into defensible "
            "release/no-release decisions for financial AI outputs. Not "
            "governance (does not define policy boundaries) and not "
            "observability (does not merely produce signals) -- this is "
            "the decision layer."
        ),
        "policy_scope": {
            "owasp_asi_coverage": ["ASI01", "ASI03"],
            "note": (
                "Deliberately narrow: ASI01 (Agent Goal Hijack) via the S1 "
                "prompt-injection test, ASI03 (Identity & Privilege Abuse) "
                "via the S6 override-rejection test. No broader OWASP ASI "
                "Top 10 or regulatory-compliance claim is made."
            ),
        },
        "owner": "CongRenHuang",
        "data_classes": sorted(DOMAIN_POLICY.keys()),
        "hard_policies_not_overridable": not_overridable,
        "enforces": [p.id for p in pid.ALL],
        "deployment": {
            "region": ALLOWED_REGION,
            "platform": "Cloud Run",
        },
    }


def main() -> None:
    card = build_card()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH}")
    print(f"enforces {len(card['enforces'])} policies: {card['enforces']}")


if __name__ == "__main__":
    main()
