"""Tests for the outward-action gate's deterministic core (engine/eval/lib/outbound.py)."""
from __future__ import annotations

import textwrap

import pytest

from lib import outbound
from lib.outbound import GateError


# --- canonicalize / digest (KTD2) -------------------------------------------

def test_key_order_does_not_change_digest():
    assert outbound.digest({"a": 1, "b": 2}) == outbound.digest({"b": 2, "a": 1})


def test_whitespace_is_trimmed():
    assert outbound.digest({"body": "hello"}) == outbound.digest({"body": "  hello  "})


def test_email_case_normalized():
    assert outbound.digest({"to": "Alice@Example.COM"}) == outbound.digest({"to": "alice@example.com"})


def test_equivalent_timestamps_same_digest():
    # Same instant, two timezone representations -> same canonical UTC -> same digest.
    a = {"start": "2026-06-10T12:00:00+00:00"}
    b = {"start": "2026-06-10T08:00:00-04:00"}
    assert outbound.digest(a) == outbound.digest(b)
    # And the trailing-Z form too.
    assert outbound.digest(a) == outbound.digest({"start": "2026-06-10T12:00:00Z"})


def test_naive_timestamp_left_alone():
    # No tzinfo -> we don't invent a zone; differing naive strings stay distinct.
    assert outbound.digest({"start": "2026-06-10T12:00:00"}) != outbound.digest({"start": "2026-06-10T08:00:00"})


def test_nested_and_nonascii_args():
    d1 = outbound.digest({"x": {"k": [1, "  é  "]}})
    d2 = outbound.digest({"x": {"k": [1, "é"]}})
    assert d1 == d2


def test_empty_args():
    assert outbound.digest({}) == outbound.digest(None)


# --- is_outward (KTD8 / R6) -------------------------------------------------

PATTERNS = ["mcp__*__create_event", "mcp__*__update_event", "mcp__*__*send*"]


def test_outward_verb_matches():
    assert outbound.is_outward("mcp__claude_ai_Google_Calendar__create_event", PATTERNS)


def test_read_verb_does_not_match():
    assert not outbound.is_outward("mcp__claude_ai_Google_Calendar__list_events", PATTERNS)
    assert not outbound.is_outward("mcp__claude_ai_Gmail__search_threads", PATTERNS)


def test_send_substring_matches():
    assert outbound.is_outward("mcp__claude_ai_Gmail__send_message", PATTERNS)


# --- find_approved_match (KTD3 / R2 / R5) -----------------------------------

TOOL = "mcp__claude_ai_Google_Calendar__create_event"


def _proposal(args: dict, *, status="approved", tool=TOOL, reversibility="reversible",
              digest_override=None, pid="prop-1"):
    args_digest = digest_override if digest_override is not None else outbound.digest(args)
    import json
    return textwrap.dedent(f"""\
        ---
        type: proposal
        id: {pid}
        status: {status}
        reversibility: {reversibility}
        tool: {tool}
        args_digest: {args_digest}
        ---

        # Proposal: test

        ## Action

        ```json
        {json.dumps(args)}
        ```
        """)


def _write_proposal(queue_dir, name, content):
    outbox = queue_dir / "outbound"
    outbox.mkdir(parents=True, exist_ok=True)
    (outbox / name).write_text(content, encoding="utf-8")


def test_matching_approved_proposal_found(tmp_path):
    args = {"summary": "Sync", "start": "2026-06-10T12:00:00+00:00"}
    _write_proposal(tmp_path, "p1.md", _proposal(args))
    match = outbound.find_approved_match(tmp_path, TOOL, outbound.digest(args))
    assert match is not None
    assert match.reversibility == "reversible"


def test_pending_proposal_does_not_match(tmp_path):
    args = {"summary": "Sync"}
    _write_proposal(tmp_path, "p1.md", _proposal(args, status="pending"))
    assert outbound.find_approved_match(tmp_path, TOOL, outbound.digest(args)) is None


def test_edited_body_fails_match(tmp_path):
    # Stored digest reflects the original args; the Action block was edited after approval.
    args = {"summary": "Sync"}
    edited = {"summary": "Sync but changed"}
    content = _proposal(args)  # frontmatter args_digest = digest(args)
    content = content.replace('{"summary": "Sync"}', '{"summary": "Sync but changed"}')
    _write_proposal(tmp_path, "p1.md", content)
    # A call matching the *edited* body must not be authorized (stored digest != edited digest).
    assert outbound.find_approved_match(tmp_path, TOOL, outbound.digest(edited)) is None
    # And a call matching the stored digest is rejected too (body re-digest != stored).
    assert outbound.find_approved_match(tmp_path, TOOL, outbound.digest(args)) is None


def test_wrong_tool_does_not_match(tmp_path):
    args = {"summary": "Sync"}
    _write_proposal(tmp_path, "p1.md", _proposal(args, tool="mcp__x__delete_event"))
    assert outbound.find_approved_match(tmp_path, TOOL, outbound.digest(args)) is None


def test_unreadable_queue_raises(tmp_path):
    # outbound/ is a file, not a dir -> glob raises -> GateError (caller denies).
    (tmp_path / "outbound").write_text("not a dir", encoding="utf-8")
    with pytest.raises(GateError):
        outbound.find_approved_match(tmp_path, TOOL, "deadbeef")


def test_missing_action_block_raises(tmp_path):
    args = {"summary": "Sync"}
    content = _proposal(args).split("## Action")[0]  # strip the json block
    _write_proposal(tmp_path, "p1.md", content)
    with pytest.raises(GateError):
        outbound.find_approved_match(tmp_path, TOOL, outbound.digest(args))


# --- tokens (U4 / R3) -------------------------------------------------------

def test_token_mint_consume_once(tmp_path):
    d = outbound.digest({"x": 1})
    outbound.mint_token(tmp_path, "prop-1", d)
    assert outbound.consume_token(tmp_path, "prop-1", d) is True
    # second consume of the same id fails -> no double send
    assert outbound.consume_token(tmp_path, "prop-1", d) is False


def test_token_digest_mismatch_not_consumed(tmp_path):
    outbound.mint_token(tmp_path, "prop-1", "aaa")
    assert outbound.consume_token(tmp_path, "prop-1", "bbb") is False
    # token survives a mismatched attempt (still present for the correct digest)
    assert outbound.consume_token(tmp_path, "prop-1", "aaa") is True


def test_missing_token_not_consumed(tmp_path):
    assert outbound.consume_token(tmp_path, "nope", "aaa") is False
