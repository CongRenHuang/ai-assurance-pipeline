"""CLI to resolve a pending approval from a separate process/terminal.

    python -m assurance.resolve ASMT-042 --decision APPROVE --reviewer dennis
"""
from __future__ import annotations
import argparse

from .approval_store import resolve


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve a pending approval.")
    parser.add_argument("assessment_id")
    parser.add_argument("--decision", required=True, choices=["APPROVE", "REJECT"])
    parser.add_argument("--reviewer", required=True)
    args = parser.parse_args()

    row = resolve(args.assessment_id, args.decision, args.reviewer)
    print(f"{row['assessment_id']}  {row['status']}  "
          f"created_at={row['created_at']}  resolved_at={row['resolved_at']}  "
          f"reviewer={row['reviewer']}")


if __name__ == "__main__":
    main()
