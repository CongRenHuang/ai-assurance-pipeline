"""Unified env loading.

load_dotenv() with no args relies on caller's __file__ to locate .env.
Under `python - <<EOF` (stdin), __file__ is "<stdin>", the path doesn't
exist, and find_dotenv()'s frame walk hits an AssertionError. This module
walks up from cwd instead, so it works under stdin, REPL, pytest, and real .py files.
"""
from __future__ import annotations
import os
from pathlib import Path

_LOADED = False


def project_root() -> Path:
    cur = Path.cwd().resolve()
    for d in (cur, *cur.parents):
        if (d / ".env").is_file() or (d / "pyproject.toml").is_file():
            return d
    return cur


def load(required: tuple[str, ...] = ()) -> Path:
    global _LOADED
    root = project_root()
    env_path = root / ".env"
    if not _LOADED:
        from dotenv import load_dotenv
        load_dotenv(env_path if env_path.is_file() else None)
        _LOADED = True
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"missing env vars {missing}; tried loading {env_path}")
    return env_path


def model() -> str:
    load()
    return os.getenv("MODEL", "gemini-3.5-flash")


def api_key() -> str:
    load(required=("GOOGLE_API_KEY",))
    return os.environ["GOOGLE_API_KEY"]
