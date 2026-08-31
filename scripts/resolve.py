#!/usr/bin/env python
"""Thin CLI wrapper -- same as `python -m assurance.resolve`.

    python scripts/resolve.py ASMT-042 --decision APPROVE --reviewer dennis
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from assurance.resolve import main

if __name__ == "__main__":
    main()
