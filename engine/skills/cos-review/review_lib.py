"""Shared core for the decision dashboard (/cos-review).

Turns the queue the system already keeps — outbound proposals (any status),
pending questions, staged Tier-2 memory diffs — into a list of decision *cards*
the renderer paints, bucketed into tabs (To review / Queued / Working / Done) and
grouped by topic. Parses the append-only `decisions-<date>.jsonl` the surface
writes back (including free-text `note` feedback), and exposes the two
deterministic write primitives the ingest phase needs so it never hand-edits
YAML: `set_status` and `regenerate_digest`.

Canonical truth stays in Markdown (`queue/outbound/*.md`, `state/corrections.md`);
the dashboard is a derived, throwaway view. Reuses engine/eval/lib (frontmatter,
outbound.digest) rather than reimplementing the gate's contract.

Pure stdlib. No network, no outward action.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# engine/eval/lib carries the gate's frontmatter reader + digest.
_EVAL_LIB = Path(__file__).resolve().parents[2] / "eval" / "lib"
if str(_EVAL_LIB) not in sys.path:
    sys.path.insert(0, str(_EVAL_LIB))

import frontmatter  # noqa: E402
import outbound  # noqa: E402


# --- Card model -------------------------------------------------------------

class Card:
    """One thing on the board. `tab` places it (review|queued|working|done);
    `topic` groups it; `card_id` (stable across regeneration) is the round-trip key."""

    __slots__ = ("card_id", "kind", "tab", "topic", "title",
                 "source_label", "date", "fields", "decisions")

    def __init__(self, card_id, kind, tab, topic, title,
                 source_label, date, fields, decisions):
        self.card_id = card_id
        self.kind = kind                  # outbound | question | memory
        self.tab = tab                    # review | queued | working | done
        self.topic = topic
        self.title = title
        self.source_label = source_label  # eyebrow left half, e.g. INBOX
        self.date = date                  # eyebrow right half
        self.fields = fields              # context / what_happened / why / draft / …
        self.decisions = decisions

    def to_dict(self):
        return {k: getattr(self, k) for k in self.__slots__}


_SLUG = re.compile(r"[^a-z0-9]+")


def _slug(text: str) -> str:
    return _SLUG.sub("-", (text or "").lower()).strip("-") or "item"


def _first_heading(body: str) -> str:
    for line in (body or "").splitlines():
        s = line.strip()
        if s.startswith("# ") and not s.startswith("##"):
            return s[2:].strip()
    return ""


# Map a proposal's status to a board tab. `working` is an optional transient a
# runtime may set while a send is mid-flight; absent it, the tab is simply empty.
_STATUS_TAB = {
    "pending": "review",
    "feedback": "feedback",   # principal left feedback; awaiting the agent's revision + re-present
    "approved": "queued",
    "working": "working",
    "sent": "done",
    "rejected": "done",
}

# Derive a source eyebrow from the outward tool when the proposal didn't name one.
_TOOL_SOURCE = [
    ("gmail", "INBOX"), ("calendar", "CALENDAR"), ("slack", "SLACK"),
    ("drive", "DRIVE"), ("dropbox", "DROPBOX"),
]


# --- Body parsing (tolerant) ------------------------------------------------

_HEADING = re.compile(r"(?m)^##+\s*(.+?)\s*$")
_FENCE = re.compile(r"```.*?```", re.DOTALL)


def _md_sections(body: str):
    """Lowercased `## heading` -> content text, with fenced code blocks (the
    machine-readable Action JSON) stripped so prose sections never absorb them.
    Tolerant: returns {} if there are no headings."""
    out, marks = {}, list(_HEADING.finditer(body or ""))
    for i, m in enumerate(marks):
        start = m.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        content = _FENCE.sub("", body[start:end]).strip()
        out[m.group(1).strip().lower()] = content
    return out


def _bold_field(body: str, label: str):
    """Text after an inline `**Label:**` field (proposal.md's native shape)."""
    m = re.search(rf"\*\*{re.escape(label)}:\*\*\s*(.+)", body or "")
    return m.group(1).strip() if m else ""


def _blockquote(body: str):
    """First run of `> ` quoted lines (proposal.md's 'Exact text' draft)."""
    lines, grabbing, buf = (body or "").splitlines(), False, []
    for ln in lines:
        if ln.lstrip().startswith(">"):
            grabbing = True
            buf.append(ln.lstrip()[1:].strip())
        elif grabbing:
            break
    return "\n".join(buf).strip()


def _bullets(text: str):
    out = []
    for ln in (text or "").splitlines():
        s = ln.strip()
        if s.startswith(("- ", "* ")):
            out.append(s[2:].strip())
    return out


def _draft_from_action(body: str):
    """Pull a human draft from the Action JSON (body/text/message/content)."""
    try:
        args = outbound._action_args(body)
    except Exception:
        return ""
    for key in ("body", "text", "message", "content"):
        v = args.get(key) if isinstance(args, dict) else None
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _lede(body: str):
    """The intro paragraph between the `# ` title and the first section / label /
    fence — the card's one-line context when no explicit `context:` is given."""
    lines, seen_title, buf = (body or "").splitlines(), False, []
    for ln in lines:
        s = ln.strip()
        if not seen_title:
            if s.startswith("# ") and not s.startswith("##"):
                seen_title = True
            continue
        if s.startswith(("##", "**", ">", "```", "- ", "* ")):
            break
        if s:
            buf.append(s)
        elif buf:
            break
    return " ".join(buf).strip()


def _outbound_fields(meta, body):
    sec = _md_sections(body)
    context = (meta.get("context")
               or sec.get("context")
               or _lede(body)
               or _bold_field(body, "What"))
    what = sec.get("what happened") or _bold_field(body, "Why")
    why = _bullets(sec.get("why this is in the sweep", ""))
    draft = (_draft_from_action(body)
             or _blockquote(body)
             or sec.get("draft") or sec.get("draft forward", ""))
    full = (sec.get("full source") or sec.get("read full source")
            or sec.get("read full email", ""))
    notes = _bullets(sec.get("notes") or sec.get("feedback", ""))
    return {
        "context": context,
        "what_happened": what,
        "why": why,
        "draft": draft,
        "full_source": full,
        "notes": notes,        # durable feedback the principal left on prior passes
        "tool": meta.get("tool") or "(principal-only send)",
        "reversibility": meta.get("reversibility") or "reversible",
        "editable": True,
    }


def _source_for(meta):
    src = meta.get("source")
    if src:
        return str(src).upper()
    tool = (meta.get("tool") or "").lower()
    for needle, label in _TOOL_SOURCE:
        if needle in tool:
            return label
    return "OUTBOUND"


# --- Collect cards from the queue -------------------------------------------

def collect_cards(instance_dir):
    """Gather every board card. Order within a tab: outbound, questions, memory."""
    inst = Path(instance_dir)
    return (
        _collect_outbound(inst)
        + _collect_questions(inst)
        + _collect_memory(inst)
    )


def _collect_outbound(inst: Path):
    cards, outbound_dir = [], inst / "queue" / "outbound"
    if not outbound_dir.is_dir():
        return cards
    for f in sorted(outbound_dir.glob("*.md")):
        try:
            meta, body = frontmatter.parse(f)
        except Exception:
            continue  # tolerant view; the gate is the authority, not this surface
        tab = _STATUS_TAB.get(str(meta.get("status", "pending")), "review")
        decisions = {"review": ["send", "edit", "reject"],
                     "queued": ["reject"]}.get(tab, [])
        cards.append(Card(
            card_id=f"outbound:{f.stem}",
            kind="outbound",
            tab=tab,
            topic=str(meta.get("topic") or "General"),
            title=_first_heading(body) or meta.get("id") or f.stem,
            source_label=_source_for(meta),
            date=str(meta.get("date") or ""),
            fields=_outbound_fields(meta, body),
            decisions=decisions,
        ))
    return cards


def _collect_questions(inst: Path):
    cards, qfile = [], inst / "state" / "pending-questions.md"
    if not qfile.is_file():
        return cards
    try:
        text = qfile.read_text(encoding="utf-8-sig")
    except OSError:
        return cards
    for row in _markdown_rows(text):
        if len(row) < 4:
            continue
        question, why, raised, status = row[0], row[1], row[2], row[3]
        if not question or question.lower() == "question":
            continue
        done = status.lower() in ("resolved", "dismissed", "answered")
        cards.append(Card(
            card_id=f"question:{_slug(question)[:48]}",
            kind="question",
            tab="done" if done else "review",
            topic="Questions",
            title=question,
            source_label="QUESTION",
            date=raised,
            fields={"context": why, "what_happened": "", "why": [],
                    "draft": "", "full_source": "", "editable": True},
            decisions=[] if done else ["answer", "dismiss"],
        ))
    return cards


def _collect_memory(inst: Path):
    """Staged Tier-2 memory diffs (queue/review/memory/*.diff|*.md), shown as the
    RAW diff, never a summary (queue/review/README.md)."""
    cards, mem_dir = [], inst / "queue" / "review" / "memory"
    if not mem_dir.is_dir():
        return cards
    for f in sorted(list(mem_dir.glob("*.diff")) + list(mem_dir.glob("*.md"))):
        try:
            raw = f.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        cards.append(Card(
            card_id=f"memory:{f.stem}",
            kind="memory",
            tab="review",
            topic="Memory",
            title=f.stem.replace("-", " "),
            source_label="MEMORY Δ",
            date="",
            fields={"diff": raw, "editable": False},
            decisions=["approve", "reject"],
        ))
    return cards


def _markdown_rows(text: str):
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(set(c) <= {"-", ":", " "} for c in cells):  # |---|---| separator
            continue
        rows.append(cells)
    return rows


# --- Decisions round-trip ---------------------------------------------------

def parse_decisions(path):
    """Parse decisions-<date>.jsonl into dicts. One JSON object per line;
    malformed lines are skipped with a warning, never fatal. Includes `note`
    feedback rows (decision == 'note', with scope/target/text)."""
    p, out = Path(path), []
    if not p.is_file():
        return out
    for n, line in enumerate(p.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"warning: skipping malformed decision line {n}: {e}", file=sys.stderr)
            continue
        if isinstance(obj, dict) and obj.get("card_id") and obj.get("decision"):
            out.append(obj)
    return out


# --- Deterministic write primitives for the ingest phase --------------------

def set_status(proposal_path, status):
    """Rewrite a proposal's frontmatter `status:` line in place (minimal edit)."""
    if status not in ("pending", "feedback", "approved", "rejected", "sent", "working"):
        raise ValueError(f"refusing unknown status {status!r}")
    p = Path(proposal_path)
    text = p.read_text(encoding="utf-8-sig")
    new, count = re.subn(r"(?m)^(status:)[ \t]*\S.*$", rf"\1 {status}", text, count=1)
    if count == 0:
        raise ValueError(f"no status: line in {p}")
    p.write_text(new, encoding="utf-8")
    return status


def resolve_memory(instance_dir, card_id, decision):
    """Move a staged Tier-2 memory diff out of the review queue per the principal's
    decision — the dashboard never edits memory itself (only the cold path may).
    `approve` -> queue/review/memory/approved/ (the next cos-consolidate-memory run
    applies it); `reject` -> .../rejected/. Returns the new path, or None if the
    source file is already gone (idempotent re-runs are safe)."""
    if decision not in ("approve", "reject"):
        raise ValueError(f"memory decision must be approve|reject, got {decision!r}")
    stem = card_id.split(":", 1)[1] if ":" in card_id else card_id
    mem = Path(instance_dir) / "queue" / "review" / "memory"
    src = next((mem / (stem + ext) for ext in (".diff", ".md")
                if (mem / (stem + ext)).is_file()), None)
    if src is None:
        return None
    dest_dir = mem / ("approved" if decision == "approve" else "rejected")
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    src.replace(dest)
    return dest


def add_note(proposal_path, text, ts=""):
    """Append one feedback note to a proposal's `## Notes` section (newest first,
    creating the section if absent) and flip its status to `feedback` so it leaves
    'To review' for the 'Feedback' tab until the agent revises and re-presents it.
    This is the durable half of the round-trip; the dashboard shows it next render."""
    p = Path(proposal_path)
    entry = f"- {ts + ' — ' if ts else ''}{text.strip()}"
    text_all = p.read_text(encoding="utf-8-sig")
    m = re.search(r"(?m)^##+\s*Notes\s*$", text_all)
    if m:
        new = text_all[:m.end()] + "\n" + entry + text_all[m.end():]
    else:
        new = text_all.rstrip() + "\n\n## Notes\n" + entry + "\n"
    p.write_text(new, encoding="utf-8")
    set_status(p, "feedback")
    return entry


def regenerate_digest(proposal_path):
    """Recompute `args_digest` from the proposal's own Action block and rewrite
    the frontmatter line — run after an `edit` so the gate still matches."""
    p = Path(proposal_path)
    _, body = frontmatter.parse(p)
    new_digest = outbound.digest(outbound._action_args(body))
    text = p.read_text(encoding="utf-8-sig")
    new, count = re.subn(r"(?m)^(args_digest:)[ \t]*.*$", rf"\1 {new_digest}", text, count=1)
    if count == 0:
        raise ValueError(f"no args_digest: line in {p}")
    p.write_text(new, encoding="utf-8")
    return new_digest


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="decision-dashboard card/decision helpers")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect"); c.add_argument("instance_dir")
    d = sub.add_parser("decisions"); d.add_argument("path")
    s = sub.add_parser("set-status"); s.add_argument("proposal_path"); s.add_argument("status")
    g = sub.add_parser("regen-digest"); g.add_argument("proposal_path")
    nt = sub.add_parser("note"); nt.add_argument("proposal_path"); nt.add_argument("text")
    nt.add_argument("--ts", default="")
    rm = sub.add_parser("resolve-memory"); rm.add_argument("instance_dir")
    rm.add_argument("card_id"); rm.add_argument("decision")
    args = ap.parse_args()

    if args.cmd == "collect":
        print(json.dumps([c.to_dict() for c in collect_cards(args.instance_dir)], indent=2))
    elif args.cmd == "decisions":
        print(json.dumps(parse_decisions(args.path), indent=2))
    elif args.cmd == "set-status":
        print(set_status(args.proposal_path, args.status))
    elif args.cmd == "regen-digest":
        print(regenerate_digest(args.proposal_path))
    elif args.cmd == "note":
        print(add_note(args.proposal_path, args.text, args.ts))
    elif args.cmd == "resolve-memory":
        print(resolve_memory(args.instance_dir, args.card_id, args.decision))
