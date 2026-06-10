"""Deterministic core for the outward-action gate (INSTRUCTIONS.md §1).

Answers one question without an LLM: "is this outward tool call backed by a
payload-matched approved proposal?" The gate hook (engine/eval/hooks/
outbound_gate.py) wires these pure functions to a PreToolUse decision.

Two halves:
  - Matching (U2): canonicalize a tool call -> SHA-256 digest, glob-match the
    outward denylist, and find an `approved` proposal in queue/outbound/ whose
    declared `tool` + `args_digest` agree with the live call AND whose own
    Action block re-digests to that same value (tamper check).
  - Tokens (U4): irreversible actions additionally consume a single-use token
    bound to the digest, so an identical payload cannot be sent twice.

Fail-closed is the caller's job: every read here raises GateError on
malformed/unreadable input, and the hook treats GateError as DENY.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

try:  # importable as a package (from lib import outbound) or standalone (hook adds lib/ to path)
    from . import frontmatter
except ImportError:  # pragma: no cover - exercised only in standalone hook invocation
    import frontmatter  # type: ignore

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ACTION_FENCE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)
# `## Autonomy` section, then the first ```yaml block, then `level: <value>`.
_AUTONOMY = re.compile(r"##\s*Autonomy\b.*?```ya?ml\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
_LEVEL = re.compile(r"^\s*level:\s*([^\s#]+)", re.MULTILINE)


class GateError(Exception):
    """Any condition that must fail the gate closed (deny). Raised on unreadable
    config/queue, malformed proposals, or a tampered Action block."""


# --- Canonicalization + digest (KTD2) ---------------------------------------

def _norm_scalar(v):
    """Normalize one scalar so trivially-equivalent calls digest identically:
    trim strings, lowercase emails, and render any parseable instant as UTC ISO-8601."""
    if not isinstance(v, str):
        return v
    s = v.strip()
    if _EMAIL.match(s):
        return s.lower()
    iso = _as_utc_iso(s)
    return iso if iso is not None else s


def _as_utc_iso(s: str):
    """Return a canonical UTC ISO-8601 string if s parses as a datetime, else None."""
    raw = s.strip()
    if not raw:
        return None
    candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if dt.tzinfo is None:  # naive timestamp — leave it to the author, don't invent a zone
        return None
    return dt.astimezone(timezone.utc).isoformat()


def _canon(obj):
    """Recursively normalize a JSON-ish value (dicts, lists, scalars)."""
    if isinstance(obj, dict):
        return {k: _canon(obj[k]) for k in sorted(obj)}
    if isinstance(obj, list):
        return [_canon(x) for x in obj]
    return _norm_scalar(obj)


def canonicalize(args: dict) -> str:
    """Canonical JSON for a tool call's arguments: sorted keys, compact, normalized scalars."""
    return json.dumps(_canon(args or {}), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(args: dict) -> str:
    """SHA-256 hex of the canonicalized args. The gate's matching key."""
    return hashlib.sha256(canonicalize(args).encode("utf-8")).hexdigest()


# --- Autonomy dial (KTD5) ---------------------------------------------------

def read_autonomy_level(config_md_path: Path):
    """Return the `autonomy.level` string from instance/config.md, or None if the
    file exists but no level is found. Raises GateError if the file can't be read,
    so the caller fails closed rather than treating a missing dial as permissive."""
    try:
        text = Path(config_md_path).read_text(encoding="utf-8-sig")
    except OSError as e:
        raise GateError(f"cannot read config {config_md_path}: {e}") from e
    block = _AUTONOMY.search(text)
    if not block:
        return None
    m = _LEVEL.search(block.group(1))
    return m.group(1).strip() if m else None


# --- Outward classification (KTD8) ------------------------------------------

def is_outward(tool_name: str, patterns) -> bool:
    """True if the tool name matches any glob in the config denylist (mutating verbs).
    Read verbs (list_/get_/search_) match nothing and pass. Case-insensitive so a
    connector that names a verb SendMessage/Create_Event can't evade the lowercase
    denylist."""
    name = (tool_name or "").lower()
    return any(fnmatch.fnmatchcase(name, str(p).lower()) for p in (patterns or []))


# --- Proposal matching (KTD3) -----------------------------------------------

class Proposal:
    __slots__ = ("path", "id", "tool", "args_digest", "reversibility", "status")

    def __init__(self, path, id, tool, args_digest, reversibility, status):
        self.path = path
        self.id = id
        self.tool = tool
        self.args_digest = args_digest
        self.reversibility = reversibility
        self.status = status


def _action_args(body: str):
    """Extract the first ```json fenced block from a proposal body. Raise GateError
    if it's absent or unparseable — a proposal with no machine-readable action can
    never authorize a call."""
    m = _ACTION_FENCE.search(body or "")
    if not m:
        raise GateError("proposal has no ```json Action block")
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise GateError(f"proposal Action block is not valid JSON: {e}") from e


def find_approved_match(queue_dir: Path, tool_name: str, call_digest: str):
    """Return the approved Proposal authorizing this exact call, or None.

    A match requires, for some queue/outbound/*.md file:
      status == approved, tool == tool_name,
      stored args_digest == call_digest (the live call matches what was approved),
      and digest(its own Action args) == stored args_digest (the proposal wasn't
      edited after approval without regenerating the digest — R2 tamper check).

    Raises GateError if the queue dir is unreadable, so the caller fails closed.
    """
    outbound = Path(queue_dir) / "outbound"
    if outbound.exists() and not outbound.is_dir():
        raise GateError(f"queue path {outbound} exists but is not a directory")
    try:
        files = sorted(outbound.glob("*.md"))
    except OSError as e:
        raise GateError(f"cannot read queue dir {outbound}: {e}") from e

    for f in files:
        try:
            meta, body = frontmatter.parse(f)
        except OSError as e:
            raise GateError(f"cannot read proposal {f}: {e}") from e
        if meta.get("status") != "approved":
            continue
        if meta.get("tool") != tool_name:
            continue
        stored = meta.get("args_digest")
        if not stored or stored != call_digest:
            continue
        if digest(_action_args(body)) != stored:  # tamper / stale-digest -> not a valid authorization
            continue
        return Proposal(
            path=f,
            id=meta.get("id") or f.stem,
            tool=tool_name,
            args_digest=stored,
            reversibility=(meta.get("reversibility") or "reversible"),
            status="approved",
        )
    return None


# --- Single-use consumption for ALL matched proposals (R2) ------------------

def mark_sent(proposal_path: Path) -> None:
    """Flip a matched proposal's status `approved` -> `sent` so the same approval
    cannot authorize a second outward call (R2: one approval = one action — for
    reversible actions too, not only irreversible). Semantics: the gate authorizes
    one *attempt*; a send that fails needs re-approval (the safe direction).

    Raises GateError on any failure, so the caller denies rather than allowing an
    unbounded replay."""
    p = Path(proposal_path)
    try:
        text = p.read_text(encoding="utf-8-sig")
    except OSError as e:
        raise GateError(f"cannot read proposal to mark sent ({p}): {e}") from e
    new = re.sub(r"(?m)^(status:\s*)approved\b", r"\1sent", text, count=1)
    if new == text:
        raise GateError(f"could not flip status approved->sent in {p}")
    try:
        p.write_text(new, encoding="utf-8")
    except OSError as e:
        raise GateError(f"cannot write proposal to mark sent ({p}): {e}") from e


# --- Single-use tokens for irreversible actions (U4 / KTD4) -----------------

def _tokens_dir(queue_dir: Path) -> Path:
    return Path(queue_dir) / "outbound" / ".tokens"


def token_path(queue_dir: Path, proposal_id: str) -> Path:
    return _tokens_dir(queue_dir) / str(proposal_id)


def mint_token(queue_dir: Path, proposal_id: str, args_digest: str) -> Path:
    """Write a single-use token binding a proposal id to its approved digest.
    Called when an irreversible proposal is approved."""
    p = token_path(queue_dir, proposal_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(args_digest, encoding="utf-8")
    return p


def consume_token(queue_dir: Path, proposal_id: str, args_digest: str) -> bool:
    """Verify a single-use token matches the digest, delete it, and return True.
    Missing, mismatched, or unreadable token -> False (caller denies). Deleting
    before returning makes a second identical send impossible (R3)."""
    p = token_path(queue_dir, proposal_id)
    try:
        stored = p.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    if stored != args_digest:
        return False
    try:
        p.unlink()
    except OSError:
        return False
    return True
