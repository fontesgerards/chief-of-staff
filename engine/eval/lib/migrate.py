"""One-time schema migration — the mechanical transforms (plan U9, R13, KTD3).

Pure text functions consumed by `cos-consolidate-memory`'s migration procedure
(and its tests). Deterministic where mechanical, and ONLY where mechanical:

- `migrate_frontmatter(text)` — `created:` → `date:` key rename (skipped when a
  `date:` key already exists — that conflict is a judgment call, Tier 2) and
  quoting of bare `covers:` date ranges. Nothing else. Fact-line reformatting
  is prose, NOT mechanically safe — it is LLM work in the skill (Tier 1
  format-only: content, values, origins, and dates never change).
- `migration_worklist(manifest_text)` — per-file paths from a findings manifest
  (`engine/validate_instance.py --manifest`), the KTD7 pipeline's work queue.
- `is_migrated(config_text)` / `mark_declined` / `parse_declined` — the
  `schema:` completion watermark and the explicit declined state (R13).

Idempotency contract: an empty `changes` list from `migrate_frontmatter` means
"already done" — that is the interrupted-resume skip signal.
"""
from __future__ import annotations

import re

# Top-level frontmatter keys only (column 0) — indented/nested keys never match.
_CREATED = re.compile(r"^created:(\s*)(.*)$")
_DATE_KEY = re.compile(r"^date:")
_COVERS_BARE = re.compile(
    r"^covers:(\s*)(\d{4}-\d{2}-\d{2}/\d{4}-\d{2}-\d{2})(\s*(?:#.*)?)$")
_SCHEMA = re.compile(r"^schema:\s*(\d+)\s*(?:#.*)?$")
_MIGRATION = re.compile(r"^migration:\s*(\S+)\s*(?:#.*)?$")
_WATERMARK = re.compile(r"^migration_watermark:\s*(\S+)\s*(?:#.*)?$")
# `- <fingerprint> | severity | file | check | detail | first_seen: …`
_FINDING = re.compile(r"^- [0-9a-f]{8,} \| \S+ \| (\S+) \| (\S+) \|")


def _split_fm(text: str):
    """Return (lines, fm_start=1, fm_end) or (lines, None, None) when no frontmatter."""
    if not text.startswith("---"):
        return text.split("\n"), None, None
    lines = text.split("\n")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines, 1, i
    return lines, None, None


def migrate_frontmatter(text: str) -> tuple[str, list[str]]:
    """Apply the mechanical U1 transforms to one file's frontmatter.

    Returns (new_text, changes). `changes == []` ⇒ nothing to do (already
    migrated, no frontmatter, or only non-mechanical work remains). The body
    is never touched.
    """
    lines, start, end = _split_fm(text)
    if start is None:
        return text, []
    changes: list[str] = []
    has_date = any(_DATE_KEY.match(ln) for ln in lines[start:end])
    new_fm = []
    for ln in lines[start:end]:
        m = _CREATED.match(ln)
        if m and not has_date:
            new_fm.append("date:" + m.group(1) + m.group(2))
            changes.append("created→date")
            has_date = True
            continue
        m = _COVERS_BARE.match(ln)
        if m:
            new_fm.append(f'covers:{m.group(1)}"{m.group(2)}"{m.group(3)}')
            changes.append("quoted covers range")
            continue
        new_fm.append(ln)
    if not changes:
        return text, []
    return "\n".join(lines[:start] + new_fm + lines[end:]), changes


def migration_worklist(findings_manifest_text: str) -> list[str]:
    """Per-file work queue from a findings manifest (manifest order, deduped).

    The `schema_gate` line on config.md is the migration *trigger*, not a work
    item — it is skipped. The skill orders the result smallest-file-first.
    """
    seen: list[str] = []
    for line in findings_manifest_text.splitlines():
        m = _FINDING.match(line.strip())
        if not m:
            continue
        path, check = m.group(1), m.group(2)
        if check == "schema_gate":
            continue
        if path not in seen:
            seen.append(path)
    return seen


def is_migrated(config_text: str) -> bool:
    """True iff config.md frontmatter carries `schema:` >= 1 (KTD3 watermark)."""
    lines, start, end = _split_fm(config_text)
    if start is None:
        return False
    for ln in lines[start:end]:
        m = _SCHEMA.match(ln)
        if m:
            return int(m.group(1)) >= 1
    return False


def mark_declined(config_text: str, watermark: str | None) -> str:
    """Pin the declined state (R13) into config.md frontmatter.

    Writes `migration: declined` plus `migration_watermark: <last-transformed
    -file-or-none>` — files at/below the watermark are already new-format, so
    the partial state stays visible. Updates in place when re-marked.
    """
    lines, start, end = _split_fm(config_text)
    if start is None:
        raise ValueError("config.md has no frontmatter block to mark")
    wm = watermark if watermark else "none"
    fm = [ln for ln in lines[start:end]
          if not _MIGRATION.match(ln) and not _WATERMARK.match(ln)]
    fm += ["migration: declined", f"migration_watermark: {wm}"]
    return "\n".join(lines[:start] + fm + lines[end:])


def parse_declined(config_text: str) -> tuple[bool, str | None]:
    """Return (declined, watermark). Watermark `none`/absent ⇒ None."""
    lines, start, end = _split_fm(config_text)
    if start is None:
        return False, None
    declined, watermark = False, None
    for ln in lines[start:end]:
        m = _MIGRATION.match(ln)
        if m:
            declined = m.group(1).strip().lower() == "declined"
        m = _WATERMARK.match(ln)
        if m:
            v = m.group(1).strip()
            watermark = None if v.lower() == "none" else v
    return declined, watermark
