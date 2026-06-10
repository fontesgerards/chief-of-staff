"""Integration tests for the outward-action gate hook.

Invokes the hook as a real subprocess (stdin JSON payload -> exit code), exercising
the same contract Claude Code uses: exit 0 = allow, exit 2 = deny. Asserts the
success criteria from the plan (docs/plans/2026-06-10-001-feat-outward-action-gate-plan.md).
"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "outbound_gate.py"
LIB = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(LIB.parent))
from lib import outbound  # noqa: E402

TOOL = "mcp__claude_ai_Google_Calendar__create_event"


def _run(payload: dict, project_dir: Path):
    """Run the hook with payload on stdin; return (returncode, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(project_dir), "PATH": ""},
    )
    return proc.returncode, proc.stderr


def _instance(tmp_path, level):
    inst = tmp_path / "instance"
    (inst / "queue" / "outbound").mkdir(parents=True)
    (inst / "config.md").write_text(textwrap.dedent(f"""\
        ---
        type: config
        ---
        # config.md
        ## Autonomy
        ```yaml
        autonomy:
          level: {level}
        ```
        """), encoding="utf-8")
    return inst


def _approve(inst, args, *, reversibility="reversible", pid="prop-1", tool=TOOL):
    args_digest = outbound.digest(args)
    (inst / "queue" / "outbound" / f"{pid}.md").write_text(textwrap.dedent(f"""\
        ---
        type: proposal
        id: {pid}
        status: approved
        reversibility: {reversibility}
        tool: {tool}
        args_digest: {args_digest}
        ---
        # Proposal
        ## Action
        ```json
        {json.dumps(args)}
        ```
        """), encoding="utf-8")
    return args_digest


def _call(args, tool=TOOL):
    return {"tool_name": tool, "tool_input": args}


# --- success criteria -------------------------------------------------------

def test_outward_call_without_proposal_denied(tmp_path):
    inst = _instance(tmp_path, "act-on-reversible")
    rc, err = _run(_call({"summary": "Sync"}), tmp_path)
    assert rc == 2
    assert "proposal" in err.lower()  # R9: self-correct message points at the queue


def test_matched_reversible_allowed(tmp_path):
    inst = _instance(tmp_path, "act-on-reversible")
    args = {"summary": "Sync", "start": "2026-06-10T12:00:00+00:00"}
    _approve(inst, args)
    rc, _ = _run(_call(args), tmp_path)
    assert rc == 0


def test_reversible_replay_denied(tmp_path):
    # R2: one approval authorizes exactly one action — even a reversible one.
    inst = _instance(tmp_path, "act-on-reversible")
    args = {"summary": "Sync"}
    _approve(inst, args)
    rc1, _ = _run(_call(args), tmp_path)
    assert rc1 == 0           # first call consumes the approval (status -> sent)
    rc2, _ = _run(_call(args), tmp_path)
    assert rc2 == 2           # identical replay finds no approved proposal


def test_act_ask_on_risky_is_permissive(tmp_path):
    # The second permissive dial advertised in the config must also allow a match.
    inst = _instance(tmp_path, "act-ask-on-risky")
    args = {"summary": "Sync"}
    _approve(inst, args)
    rc, _ = _run(_call(args), tmp_path)
    assert rc == 0


def test_matched_but_propose_only_denied(tmp_path):
    inst = _instance(tmp_path, "propose-only")
    args = {"summary": "Sync"}
    _approve(inst, args)
    rc, err = _run(_call(args), tmp_path)
    assert rc == 2  # R4: even an approved+matched call is blocked at the default dial
    assert "propose-only" in err


def test_read_verb_allowed(tmp_path):
    inst = _instance(tmp_path, "propose-only")
    rc, _ = _run(_call({}, tool="mcp__claude_ai_Google_Calendar__list_events"), tmp_path)
    assert rc == 0  # R6


def test_edited_proposal_fails_match(tmp_path):
    inst = _instance(tmp_path, "act-on-reversible")
    _approve(inst, {"summary": "Sync"})
    rc, err = _run(_call({"summary": "Sync but tampered"}), tmp_path)
    assert rc == 2  # R2
    assert "no approved proposal matches" in err  # denied for the right reason, not a config error


def test_missing_config_denied(tmp_path):
    (tmp_path / "instance" / "queue" / "outbound").mkdir(parents=True)
    # no config.md
    rc, err = _run(_call({"summary": "Sync"}), tmp_path)
    assert rc == 2  # R5 fail-closed
    assert "autonomy dial" in err  # bound to the dial-read failure, not some other deny


def test_irreversible_allowed_once_then_denied(tmp_path):
    inst = _instance(tmp_path, "act-on-reversible")
    args = {"to": "ceo@example.com", "body": "wire the funds"}
    d = _approve(inst, args, reversibility="irreversible", pid="irr-1")
    outbound.mint_token(inst / "queue", "irr-1", d)
    rc1, _ = _run(_call(args), tmp_path)
    assert rc1 == 0          # first send: token consumed
    rc2, _ = _run(_call(args), tmp_path)
    assert rc2 == 2          # R3: identical replay denied — token already burned


def test_irreversible_without_token_denied(tmp_path):
    inst = _instance(tmp_path, "act-on-reversible")
    args = {"to": "ceo@example.com", "body": "wire the funds"}
    _approve(inst, args, reversibility="irreversible", pid="irr-2")
    # no token minted
    rc, err = _run(_call(args), tmp_path)
    assert rc == 2
    assert "token" in err.lower()  # bound to the token requirement, not a config/match error


def test_real_config_breadth():
    # Pin the shipped denylist + permissive levels so a future edit can't silently
    # un-gate a tool or make propose-only permissive (the config's own warning).
    import json as _json
    cfg = _json.loads((HOOK.parent / "outbound_gate.config.json").read_text(encoding="utf-8"))
    patterns = cfg["outward_tool_patterns"]
    assert outbound.is_outward("mcp__claude_ai_Google_Calendar__create_event", patterns)
    assert outbound.is_outward("mcp__claude_ai_Gmail__send_message", patterns)
    assert outbound.is_outward("mcp__claude_ai_Google_Drive__copy_file", patterns)
    assert not outbound.is_outward("mcp__claude_ai_Google_Calendar__list_events", patterns)
    assert "propose-only" not in cfg["permissive_autonomy_levels"]


def test_empty_stdin_allows(tmp_path):
    inst = _instance(tmp_path, "propose-only")
    proc = subprocess.run(
        [sys.executable, str(HOOK)], input="", capture_output=True, text=True,
        env={"CLAUDE_PROJECT_DIR": str(tmp_path), "PATH": ""},
    )
    assert proc.returncode == 0  # no tool_name -> nothing to gate
