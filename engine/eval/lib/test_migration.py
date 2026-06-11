"""Tests for the one-time schema migration (plan U9, R13, R14, KTD3).

Written FIRST, per the plan's execution note: the legacy → expected pairs here
pin the mechanical transform's exact semantics before any procedure text.

Mechanical scope (engine/eval/lib/migrate.py) is deliberately tiny:
  - `created:` → `date:` key rename (only when `date:` is absent — else ambiguous)
  - quote unquoted `covers:` date ranges
Fact-line reformatting is NOT mechanically safe (it lives in prose) — it is LLM
work in the cos-consolidate-memory skill, and these tests pin that the
mechanical transform never touches the body.
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

from lib import frontmatter, migrate

REPO = Path(__file__).resolve().parents[3]
GOLDEN = REPO / "engine" / "eval" / "scenarios" / "01-write-back-loop" / "golden"
SKILLS = REPO / "engine" / "skills"

# The production sweep CLI (worklist producer) — loaded by path like test_validate.py.
_spec = importlib.util.spec_from_file_location(
    "validate_instance_m", REPO / "engine" / "validate_instance.py")
vi = importlib.util.module_from_spec(_spec)
sys.modules["validate_instance_m"] = vi
_spec.loader.exec_module(vi)


# --- fixtures: legacy → expected pairs (the transform's contract) ---------------

LEGACY_COACHING = """\
---
type: coaching-note
created: 2026-05-20          # the run date
covers: 2026-05-13/2026-05-20
origin: derived
---

# Coaching — week of 2026-05-20

## Moves (one or two — not a list)
- In the Plata call you anchored on price too early.
"""

EXPECTED_COACHING = """\
---
type: coaching-note
date: 2026-05-20          # the run date
covers: "2026-05-13/2026-05-20"
origin: derived
---

# Coaching — week of 2026-05-20

## Moves (one or two — not a list)
- In the Plata call you anchored on price too early.
"""

# Old-style fact line in the body — prose, NOT mechanically transformable.
LEGACY_PERSON_BODY = """\
---
type: person
status: active
last_touched: 2026-05-01
relationships: []
confidence: 75
origin: imported
sources: []
created: 2026-04-01
---

# Andre Maligian

## Facts
- Reports to Maya (origin: imported, valid_until: 2026-05-01)
- CTO since 2026-05 (origin: confirmed)
"""

# No schema marker, no frontmatter changes needed at all.
NO_MARKER_CONFIG = """\
---
type: config
date: 2026-05-01
---

# config.md
"""


# --- mechanical transforms: legacy → expected equality ----------------------------

def test_created_renamed_to_date_exact():
    out, changes = migrate.migrate_frontmatter(LEGACY_COACHING)
    assert out == EXPECTED_COACHING
    assert "created→date" in changes
    assert "quoted covers range" in changes


def test_covers_quoting_preserves_inline_comment():
    legacy = '---\ntype: research-digest\ndate: 2026-06-01\ncovers: 2026-05-25/2026-06-01   # the week scanned\norigin: derived\n---\nbody\n'
    out, changes = migrate.migrate_frontmatter(legacy)
    assert 'covers: "2026-05-25/2026-06-01"   # the week scanned' in out
    assert changes == ["quoted covers range"]


def test_already_quoted_covers_untouched():
    text = '---\ntype: research-digest\ndate: 2026-06-01\ncovers: "2026-05-25/2026-06-01"\norigin: derived\n---\nbody\n'
    out, changes = migrate.migrate_frontmatter(text)
    assert out == text and changes == []


def test_created_alongside_existing_date_is_ambiguous_not_mechanical():
    """Both keys present → which wins is a judgment call → no mechanical edit."""
    text = '---\ntype: episode\ndate: 2026-06-01\ncreated: 2026-05-30\norigin: observed\n---\nbody\n'
    out, changes = migrate.migrate_frontmatter(text)
    assert out == text and changes == []


def test_body_fact_lines_never_touched():
    """Old fact-line style `(origin: imported, valid_until: …)` is prose — LLM work
    in the skill (Tier 1 format-only), never the mechanical transform."""
    out, changes = migrate.migrate_frontmatter(LEGACY_PERSON_BODY)
    assert changes == ["created→date"]
    _, body = frontmatter.split_frontmatter(out)
    _, legacy_body = frontmatter.split_frontmatter(LEGACY_PERSON_BODY)
    assert body == legacy_body  # byte-identical body
    assert "- Reports to Maya (origin: imported, valid_until: 2026-05-01)" in out


def test_no_frontmatter_and_clean_files_are_no_ops():
    assert migrate.migrate_frontmatter("just prose\n") == ("just prose\n", [])
    out, changes = migrate.migrate_frontmatter(NO_MARKER_CONFIG)
    assert out == NO_MARKER_CONFIG and changes == []


# --- idempotency: running twice == running once -----------------------------------

def test_idempotent():
    once, changes1 = migrate.migrate_frontmatter(LEGACY_COACHING)
    twice, changes2 = migrate.migrate_frontmatter(once)
    assert twice == once
    assert changes1 and changes2 == []  # empty `changes` is the already-done signal


# --- interrupted-resume: 2 of 4 done, re-run completes without re-editing ----------

def test_interrupted_resume(tmp_path):
    files = []
    for i in range(4):
        p = tmp_path / f"note-{i}.md"
        p.write_text(LEGACY_COACHING, encoding="utf-8")
        files.append(p)
    # First pass is interrupted after 2 files.
    for p in files[:2]:
        out, changes = migrate.migrate_frontmatter(p.read_text(encoding="utf-8"))
        assert changes
        p.write_text(out, encoding="utf-8")
    # Resume over the FULL worklist: done files report no changes (skip signal),
    # the remaining two transform; nothing is re-edited.
    edited = []
    for p in files:
        out, changes = migrate.migrate_frontmatter(p.read_text(encoding="utf-8"))
        if changes:
            edited.append(p.name)
            p.write_text(out, encoding="utf-8")
    assert edited == ["note-2.md", "note-3.md"]
    for p in files:
        assert p.read_text(encoding="utf-8") == EXPECTED_COACHING


# --- worklist from the findings manifest (KTD7 pipeline) ----------------------------

MANIFEST = """\
---
type: validation-findings
date: 2026-06-11
schema_seen: null
---

# Validation findings — 2026-06-11

Instance: `/tmp/x` · mode: legacy · 3 error(s), 0 warn(s), 2 file(s) swept.

- aaaaaaaa | error | config.md | schema_gate | migration pending — legacy remainder not swept (config.md `schema:` missing or < 1) | first_seen: 2026-06-11
- bbbbbbbb | error | memory/episodic/coaching/2026-05-20.md | required_keys | missing required frontmatter key 'date' (type: coaching-note) | first_seen: 2026-06-11
- cccccccc | error | memory/episodic/coaching/2026-05-20.md | required_keys | missing required frontmatter key 'covers' (type: coaching-note) | first_seen: 2026-06-11
- dddddddd | error | memory/semantic/people/andre.md | has_origin | origin 'vibes' not in enum | first_seen: 2026-06-11
"""


def test_worklist_dedups_and_skips_schema_gate():
    paths = migrate.migration_worklist(MANIFEST)
    # config.md's schema_gate line is the trigger, not a work item; dupes collapse.
    assert paths == [
        "memory/episodic/coaching/2026-05-20.md",
        "memory/semantic/people/andre.md",
    ]


def test_worklist_empty_on_clean_manifest():
    assert migrate.migration_worklist("# Validation findings\n\n(no findings)\n") == []


def test_worklist_keeps_paths_with_spaces():
    """Manifest columns are ` | `-delimited — a file path containing spaces must
    survive into the worklist, not be truncated or dropped by a \\S+ match."""
    manifest = (
        "- aaaaaaaa | error | memory/semantic/accounts/holland america.md | "
        "required_keys | missing required frontmatter key 'date' | first_seen: 2026-06-11\n"
        "- bbbbbbbb | error | memory/episodic/coaching/2026-05-20.md | "
        "has_origin | origin 'vibes' not in enum | first_seen: 2026-06-11\n"
    )
    assert migrate.migration_worklist(manifest) == [
        "memory/semantic/accounts/holland america.md",
        "memory/episodic/coaching/2026-05-20.md",
    ]


# --- schema marker + declined state -------------------------------------------------

def test_is_migrated():
    assert migrate.is_migrated("---\ntype: config\nschema: 1\n---\nbody\n")
    assert migrate.is_migrated("---\nschema: 2\n---\n")
    assert not migrate.is_migrated(NO_MARKER_CONFIG)        # marker absent
    assert not migrate.is_migrated("---\nschema: 0\n---\n")  # < 1
    assert not migrate.is_migrated("no frontmatter at all\n")


def test_declined_watermark_roundtrip():
    marked = migrate.mark_declined(NO_MARKER_CONFIG, "memory/episodic/coaching/2026-05-20.md")
    declined, watermark = migrate.parse_declined(marked)
    assert declined and watermark == "memory/episodic/coaching/2026-05-20.md"
    # Declined before any file was transformed → watermark is none → None.
    marked_none = migrate.mark_declined(NO_MARKER_CONFIG, None)
    declined2, watermark2 = migrate.parse_declined(marked_none)
    assert declined2 and watermark2 is None
    # Pristine config: not declined.
    assert migrate.parse_declined(NO_MARKER_CONFIG) == (False, None)
    # Marking twice updates in place (idempotent keys, no duplicate lines).
    remarked = migrate.mark_declined(marked, "memory/semantic/people/andre.md")
    assert remarked.count("migration: declined") == 1
    assert remarked.count("migration_watermark:") == 1
    assert migrate.parse_declined(remarked) == (True, "memory/semantic/people/andre.md")


def test_declined_watermark_roundtrip_with_spaces():
    """A watermark path containing spaces must roundtrip mark_declined →
    parse_declined intact (capture to end of line, not \\S+)."""
    spaced = "memory/semantic/accounts/holland america.md"
    marked = migrate.mark_declined(NO_MARKER_CONFIG, spaced)
    assert migrate.parse_declined(marked) == (True, spaced)
    # Re-marking with another spaced path updates in place, no duplicate lines.
    respaced = "memory/semantic/people/jeremy roy.md"
    remarked = migrate.mark_declined(marked, respaced)
    assert remarked.count("migration_watermark:") == 1
    assert migrate.parse_declined(remarked) == (True, respaced)


def test_bom_prefixed_legacy_file_transforms():
    """A leading UTF-8 BOM must not hide the frontmatter — the legacy file is
    transformed (matching frontmatter.py's utf-8-sig tolerance), and a second
    run is a no-op."""
    bom_legacy = "\ufeff" + LEGACY_COACHING
    out, changes = migrate.migrate_frontmatter(bom_legacy)
    assert "created→date" in changes and "quoted covers range" in changes
    assert out == EXPECTED_COACHING  # BOM dropped, transform applied
    again, changes2 = migrate.migrate_frontmatter(out)
    assert again == out and changes2 == []


def test_quoted_tokens_match_unquoted_semantics():
    """`migration: "declined"` and `schema: "1"` are the same scalars as their
    bare forms under pyyaml — quotes must be stripped from captured tokens."""
    for quote in ('"', "'"):
        assert migrate.is_migrated(f"---\ntype: config\nschema: {quote}1{quote}\n---\nbody\n")
        assert not migrate.is_migrated(f"---\nschema: {quote}0{quote}\n---\n")
        quoted_cfg = (
            f"---\ntype: config\nmigration: {quote}declined{quote}\n"
            f"migration_watermark: {quote}memory/semantic/accounts/holland america.md{quote}\n---\n"
        )
        assert migrate.parse_declined(quoted_cfg) == (
            True, "memory/semantic/accounts/holland america.md")
    # Quoted `none` watermark still means None.
    assert migrate.parse_declined(
        '---\nmigration: "declined"\nmigration_watermark: "none"\n---\n') == (True, None)


def test_declined_config_is_honored_by_validate(tmp_path):
    """mark_declined output must be exactly what the sweep's suppress check reads."""
    inst = tmp_path / "instance"
    shutil.copytree(GOLDEN, inst)
    cfg = inst / "config.md"
    text = "\n".join(ln for ln in cfg.read_text(encoding="utf-8").splitlines()
                     if not ln.startswith("schema:")) + "\n"
    cfg.write_text(migrate.mark_declined(text, None), encoding="utf-8")
    rep = vi.run_validation(inst)
    assert rep["mode"] == "declined"
    assert len(rep["findings"]) == 1
    assert "suppressed by decline" in rep["findings"][0]["detail"]


# --- end-to-end: legacy instance → manifest → worklist → migrate → clean sweep -------

def test_migration_pipeline_end_to_end(tmp_path):
    inst = tmp_path / "instance"
    shutil.copytree(GOLDEN, inst)
    cfg = inst / "config.md"
    cfg.write_text(
        "\n".join(ln for ln in cfg.read_text(encoding="utf-8").splitlines()
                  if not ln.startswith("schema:")) + "\n", encoding="utf-8")
    legacy = inst / "memory" / "episodic" / "coaching" / "2026-05-20.md"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text(LEGACY_COACHING, encoding="utf-8")

    # Step 1 — full per-file sweep on the legacy instance: `--upgrade-date` set to
    # the epoch sweeps every file despite the schema gate (the worklist producer).
    rep = vi.run_validation(inst, upgrade_date="1970-01-01")
    manifest = vi.write_manifest(
        rep, inst / "state" / "validation" / "findings-2026-06-11.md",
        today="2026-06-11")

    # Step 2 — worklist from the manifest: the one legacy file, no config.md.
    worklist = migrate.migration_worklist(manifest.read_text(encoding="utf-8"))
    assert worklist == ["memory/episodic/coaching/2026-05-20.md"]

    # Step 3 — per-file mechanical transform.
    for rel in worklist:
        p = inst / rel
        out, changes = migrate.migrate_frontmatter(p.read_text(encoding="utf-8"))
        assert changes
        p.write_text(out, encoding="utf-8")
    assert legacy.read_text(encoding="utf-8") == EXPECTED_COACHING

    # Step 4 — fresh sweep of the worklist files is clean BEFORE the marker is set…
    rep2 = vi.run_validation(inst, upgrade_date="1970-01-01")
    assert [f for f in rep2["findings"] if f["check"] != "schema_gate"] == []

    # Step 5 — …and only then `schema: 1` lands (the LAST step). Full mode, zero findings.
    text = cfg.read_text(encoding="utf-8")
    cfg.write_text(text.replace("type: config", "type: config\nschema: 1", 1),
                   encoding="utf-8")
    assert migrate.is_migrated(cfg.read_text(encoding="utf-8"))
    rep3 = vi.run_validation(inst)
    assert rep3["mode"] == "full" and rep3["findings"] == []


# --- R14: daily/weekly skills carry the read-both migration-window note --------------

DAILY_SKILLS = [
    "cos-meeting-prep",
    "cos-meeting-follow-up",
    "cos-entity-enrichment",
    "cos-research",
    "cos-loop-closing",
    "cos-coaching",
    "cos-goal-setting",
]


def test_daily_skills_carry_migration_window_note():
    missing = [
        name for name in DAILY_SKILLS
        if "Migration window" not in (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
    ]
    assert not missing, f"SKILL.md missing the R14 read-both note: {missing}"
