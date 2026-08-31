"""Shared helpers for the demo recorder driver.

Everything the recorded screen shows goes through here: typed-effect
printing, ANSI highlight, and the wall-clock scheduling primitive that
keeps a segment locked to its narration mp3 instead of drifting on
accumulated sleep() error.
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAKES = ROOT / "docs" / "assets" / "takes"
SEGMENTS = ROOT / "docs" / "assets" / "segments"
CONFIG_PATH = TAKES / "take-config.json"
TIMELINE_PATH = TAKES / "take-timeline.json"

REVERSE = "\033[7m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"


def note(msg: str) -> None:
    """Operator-facing status line. Never goes to the recorded screen."""
    print(f"{DIM}[driver] {msg}{RESET}", file=sys.stderr, flush=True)


def load_config() -> dict:
    if not CONFIG_PATH.is_file():
        raise SystemExit(
            f"{CONFIG_PATH} missing -- run `python -m scripts.demo_recorder.prerun` first")
    return json.loads(CONFIG_PATH.read_text())


def save_config(cfg: dict) -> None:
    TAKES.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))


class Clock:
    """Absolute wall-clock scheduler. Never sleep-to-sleep -- always
    sleep to (segment_start + at), so per-action drift can't accumulate
    across a 30-45s segment."""

    def __init__(self) -> None:
        self.t0 = time.monotonic()

    def wait_until(self, at: float) -> None:
        remaining = self.t0 + at - time.monotonic()
        if remaining > 0:
            time.sleep(remaining)

    def elapsed(self) -> float:
        return time.monotonic() - self.t0


def clear_screen() -> None:
    print("\033[2J\033[H", end="", flush=True)


def type_line(text: str, *, cps: float = 55.0, newline: bool = True) -> None:
    """Prints text at a bounded characters-per-second rate, like someone
    actually typing it. cps is deliberately not configurable per-call
    beyond this default -- keeping one typing speed across the whole
    recording is what makes it read as one consistent take."""
    delay = 1.0 / cps
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    if newline:
        sys.stdout.write("\n")
        sys.stdout.flush()


def print_lines(lines: list[str], *, delay: float = 0.0) -> None:
    for line in lines:
        print(line)
        if delay:
            time.sleep(delay)


def highlight_reprint(lines: list[str], match_substrings: list[str]) -> None:
    """Reprints `lines`, wrapping any line containing one of
    match_substrings in reverse-video. Used for the S2/S3/S5 'highlight
    this line' beats -- screencapture can't select text with a mouse for
    us, so the recording re-emits the same content styled instead."""
    for line in lines:
        if any(s in line for s in match_substrings):
            print(f"{REVERSE}{line}{RESET}")
        else:
            print(line)


def hold(seconds: float) -> None:
    time.sleep(seconds)
