"""Parses docs/assets/takes/batch.log -- the one real batch run from
prerun.py -- into the pieces the S2/S3/S4/S5 scenes replay.

Never invents numbers. Every count, every ID, every trajectory line
the recording shows comes from this file, which is exactly what
evidence/S2-batch-run.json was built from.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParsedItem:
    raw: str
    item_id: str
    route: str


@dataclass
class BatchLog:
    items: list[ParsedItem]
    total_line: str
    table_lines: list[str]
    packet_lines: list[str]

    def by_route(self, route: str) -> list[ParsedItem]:
        return [i for i in self.items if i.route == route]


def parse(path: Path) -> BatchLog:
    lines = path.read_text(encoding="utf-8").splitlines()
    total_idx = next(i for i, l in enumerate(lines) if l.startswith("total="))

    items = []
    for line in lines[:total_idx]:
        if not line.strip():
            continue
        parts = line.split()
        items.append(ParsedItem(raw=line, item_id=parts[0], route=parts[1]))

    tail = lines[total_idx:]
    total_line = tail[0]

    packet_idx = next(
        (i for i, l in enumerate(tail) if l.startswith("=== Approval Packet")), None)
    if packet_idx is not None:
        table_lines = tail[1:packet_idx]
        packet_lines = tail[packet_idx:]
    else:
        table_lines = tail[1:]
        packet_lines = []

    table_lines = [l for l in table_lines if l.strip()]

    return BatchLog(items=items, total_line=total_line,
                     table_lines=table_lines, packet_lines=packet_lines)
