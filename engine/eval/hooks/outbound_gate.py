#!/usr/bin/env python3
"""PreToolUse outward-action gate — structural enforcement of propose-never-act.

Makes INSTRUCTIONS.md §1 structural instead of behavioral (the outward twin of
provenance_check.py): an outward connector call executes only when the autonomy
dial permits AND a payload-matched approved proposal exists in
instance/queue/outbound/. Deterministic, no LLM (write-back.md §8.2).

PreToolUse, not PostToolUse — outward sends are often irreversible, so the call
must be blocked BEFORE it runs. exit 2 = DENY (stderr surfaced to the model so it
self-corrects into writing a proposal); exit 0 = ALLOW.

FAIL-CLOSED ON CRASH: Claude Code only blocks on exit 2 — any other exit code
(including the 1 Python uses for an uncaught exception or a failed import) lets
the call PROCEED. So the entry point wraps everything: any exception, including a
failed `from lib import outbound`, is converted to a deny (exit 2). The lib import
lives inside main() for exactly this reason.

Wire via .claude/settings.json with matcher "mcp__.*" (see settings.example.json).
Resolves the instance from $CLAUDE_PROJECT_DIR (the working folder holding
instance/). Fail-closed: any unreadable config/queue/dial, or any ambiguity on an
outward call, denies. The gate config (outward denylist + permissive levels) lives
beside this file in outbound_gate.config.json (KTD8).

Coverage limit (by design): the gate sees MCP tool names only. Bash egress
(curl/osascript) and non-MCP tools are out of scope here — closed by the OS
sandbox (layer 3) and read-only OAuth scopes (layer 1). See
engine/docs/write-isolation-config.md.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parent / "outbound_gate.config.json"
PROPOSE_HINT = (
    "Do not call this tool directly. Write a proposal to instance/queue/outbound/ "
    "using engine/templates/proposal.md (fill the Action block + args_digest); it "
    "executes only after the principal approves it and the autonomy dial permits."
)


def _payload() -> dict:
    if sys.stdin.isatty():  # run manually without piped input — don't block on read
        return {}
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}


def _deny(msg: str) -> None:
    print(f"[outbound-gate DENY] {msg}", file=sys.stderr)
    sys.exit(2)


def _load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _instance_dir() -> Path:
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return Path(root) / "instance"


def main() -> int:
    # Import the lib HERE (not at module top) so an import failure is caught by the
    # entry guard and fails closed — a top-level import error would exit 1 = ALLOW.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # engine/eval -> `from lib import ...`
    from lib import outbound
    GateError = outbound.GateError

    data = _payload()
    tool_name = data.get("tool_name")
    if not tool_name:  # nothing to classify (manual/empty invocation) — let it through
        return 0

    # Config drives which tools are outward. If it can't load, fail closed: deny
    # every call that reached this hook (matcher already scoped it to MCP tools).
    try:
        cfg = _load_config()
        patterns = cfg["outward_tool_patterns"]
        permissive = set(cfg.get("permissive_autonomy_levels", []))
    except Exception as e:
        _deny(f"gate config unreadable ({CONFIG}): {e}. Refusing all gated calls until fixed.")

    if not outbound.is_outward(tool_name, patterns):
        return 0  # read verb / ungated tool — pass untouched (R6)

    # --- outward call: dial first (R4) ---
    instance = _instance_dir()
    config_md = instance / "config.md"
    try:
        level = outbound.read_autonomy_level(config_md)
    except GateError as e:
        _deny(f"{e} — cannot confirm the autonomy dial, so {tool_name} is blocked.")
    if level is None:
        _deny(f"no autonomy level found in {config_md}; {tool_name} blocked. {PROPOSE_HINT}")
    if level not in permissive:
        _deny(
            f"autonomy is '{level}' — the agent does not execute outward actions at this dial. "
            f"{PROPOSE_HINT}"
        )

    # --- payload-bound match (R1/R2) ---
    call_digest = outbound.digest(data.get("tool_input") or {})
    try:
        match = outbound.find_approved_match(instance / "queue", tool_name, call_digest)
    except GateError as e:
        _deny(f"{e} — cannot verify an approved proposal, so {tool_name} is blocked.")
    if match is None:
        _deny(
            f"no approved proposal matches this {tool_name} call (digest {call_digest[:12]}…). "
            f"{PROPOSE_HINT}"
        )

    # --- irreversible actions burn a single-use token (R3) ---
    if match.reversibility == "irreversible":
        if not outbound.consume_token(instance / "queue", match.id, call_digest):
            _deny(
                f"irreversible action '{match.id}' has no valid single-use token "
                "(already executed, or approval did not mint one). Re-approve to mint a fresh token."
            )

    # --- consume the approval so it can't authorize a second call (R2) ---
    try:
        outbound.mark_sent(match.path)
    except GateError as e:
        _deny(f"{e} — refusing to allow an unbounded replay of approval '{match.id}'.")

    return 0  # all gates passed — allow the call


if __name__ == "__main__":
    # Fail-closed boundary: a real deny raises SystemExit(2) and must propagate; any
    # OTHER exception (crash, import failure, bad payload shape) is converted to a
    # deny so the gate never fails open. A crash therefore blocks MCP calls loudly
    # (the matcher scopes this to mcp__.*; Bash/Write are unaffected).
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException as e:  # noqa: BLE001 - intentional catch-all to fail closed
        print(f"[outbound-gate DENY] gate crashed ({e!r}); refusing the call fail-closed.", file=sys.stderr)
        raise SystemExit(2)
