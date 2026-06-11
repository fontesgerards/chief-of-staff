#!/usr/bin/env python3
"""PostToolUse provenance/schema guard for COS memory writes.

Makes "structural, not scan" real (INSTRUCTIONS.md §6, write-back.md §8): instead
of trusting the model to remember the conventions, validate every Write/Edit that
lands under `instance/memory/` at write time.

Two-tier severity (after pm-brain's hook):
  BLOCK (exit 2)  — entity file with no/invalid `origin`; an unapproved edit to
                    core/ (the safety-floor tier-2 line).
  WARN  (exit 0)  — a [[wikilink]] that doesn't resolve yet (may resolve later).

Wire it via .claude/settings.json (see settings.example.json). It reads the hook
payload on stdin: {"tool_name","tool_input":{"file_path","content"},...}.
BLOCK feedback (stderr + exit 2) is surfaced to the model so it self-corrects.

Note: PostToolUse fires *after* the write, so this is a corrective guard. To make
the core/ write-ban truly preventive, pair it with a PreToolUse deny on
`Write/Edit(instance/memory/core/**)` — see engine/docs/write-isolation-config.md.
Set COS_TIER2_APPROVED=1 in the environment of an approved cold-path run to allow
core/ edits.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Self-contained by design (this hook must run with zero imports beyond stdlib).
# Keep in sync with engine/eval/lib/assertions.py:VALID_ORIGINS — test_schema.py
# asserts equality.
VALID_ORIGINS = {"observed", "confirmed", "inferred", "imported", "derived"}
WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
# Entity files carry frontmatter + origin; logs/state/queue/sources are append-only notes.
ENTITY_DIRS = ("/memory/semantic/", "/memory/episodic/", "/memory/procedural/")


def _payload() -> dict:
    if sys.stdin.isatty():  # run manually without piped input — don't block on read
        return {}
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}


def _norm(p: str) -> str:
    return p.replace("\\", "/")


def _frontmatter_origin(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    head = text[3:end] if end != -1 else ""
    for line in head.splitlines():
        if line.strip().startswith("origin:"):
            val = line.split(":", 1)[1].strip().split("#", 1)[0].strip()
            return val.strip('"').strip("'")
    return None


def _block(msg: str) -> None:
    print(f"[provenance-guard BLOCK] {msg}", file=sys.stderr)
    sys.exit(2)


def _warn(msg: str) -> None:
    print(f"[provenance-guard WARN] {msg}", file=sys.stderr)
    sys.exit(0)


def main() -> int:
    data = _payload()
    if data.get("tool_name") not in ("Write", "Edit", "MultiEdit"):
        return 0
    tin = data.get("tool_input", {}) or {}
    raw_path = tin.get("file_path") or tin.get("path") or ""
    path = _norm(raw_path)
    if "instance/memory/" not in path:  # leading-slash-agnostic: works for relative or absolute paths
        return 0  # only guard the memory store

    idx = path.find("instance/memory")
    rel = path[idx + len("instance/"):]                  # -> memory/...
    memory_root = Path(path[: idx + len("instance/memory")])  # -> .../instance/memory

    # Read the post-write content from disk; fall back to the payload's content.
    text = ""
    try:
        text = Path(raw_path).read_text(encoding="utf-8")
    except Exception:
        text = tin.get("content") or tin.get("new_string") or ""

    # --- Safety floor: core/ is Tier-2 only ---
    if "/memory/core/" in path and os.environ.get("COS_TIER2_APPROVED") != "1":
        _block(
            f"edit to core/ ({rel}) requires an approved Tier-2 "
            "proposal. Route it through instance/queue/review/ as a raw diff; an approved "
            "cold-path run sets COS_TIER2_APPROVED=1. (INSTRUCTIONS.md §9)"
        )

    # --- Provenance: entity files must declare a valid origin ---
    if any(d in path for d in ENTITY_DIRS) and path.endswith(".md"):
        origin = _frontmatter_origin(text)
        if origin is None:
            _block(f"{rel}: entity file is missing an `origin:` field. "
                   f"Add one of {sorted(VALID_ORIGINS)} to the frontmatter (INSTRUCTIONS.md §6).")
        if origin not in VALID_ORIGINS:
            _block(f"{rel}: origin={origin!r} is not in the closed set {sorted(VALID_ORIGINS)}.")

    # --- Link validity: WARN only (a link may resolve on a later write) ---
    if text:
        if memory_root.is_dir():
            stems = {p.stem.lower() for p in memory_root.rglob("*.md")}
            unresolved = sorted({
                m for m in WIKILINK.findall(text)
                if m.split("|")[0].strip().split("/")[-1].lower() not in stems
            })
            if unresolved:
                _warn(f"{rel}: unresolved [[links]]: {', '.join(unresolved)} "
                      "(ok if they're created later; the Friday sweep re-checks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
