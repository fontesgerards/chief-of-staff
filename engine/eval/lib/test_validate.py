"""Tests for the cos-validate sweep (plan U8, R12, KTD3, KTD7).

Imports the module's functions directly — no shelling out. Fixtures are tmp
copies of the 01-write-back-loop golden (a clean, migrated instance).
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
import time
from pathlib import Path

from lib import frontmatter

REPO = Path(__file__).resolve().parents[3]
GOLDEN = REPO / "engine" / "eval" / "scenarios" / "01-write-back-loop" / "golden"

# The CLI is production tooling at engine/validate_instance.py (not under eval/);
# load it by path so the tests exercise the exact shipped module.
_spec = importlib.util.spec_from_file_location(
    "validate_instance", REPO / "engine" / "validate_instance.py")
vi = importlib.util.module_from_spec(_spec)
sys.modules["validate_instance"] = vi
_spec.loader.exec_module(vi)


# --- fixture helpers -----------------------------------------------------------

def _copy_golden(tmp_path: Path) -> Path:
    inst = tmp_path / "instance"
    shutil.copytree(GOLDEN, inst)
    return inst


def _strip_schema(inst: Path) -> None:
    cfg = inst / "config.md"
    text = cfg.read_text(encoding="utf-8")
    lines = [ln for ln in text.splitlines() if not ln.startswith("schema:")]
    cfg.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _decline_migration(inst: Path) -> None:
    _strip_schema(inst)
    cfg = inst / "config.md"
    text = cfg.read_text(encoding="utf-8")
    cfg.write_text(text.replace("type: config", "type: config\nmigration: declined", 1),
                   encoding="utf-8")


def _age_all_files(inst: Path, days: int = 30) -> None:
    old = time.time() - days * 86400
    for p in inst.rglob("*"):
        if p.is_file():
            os.utime(p, (old, old))


# --- clean migrated instance → zero findings ------------------------------------

def test_clean_golden_zero_findings():
    rep = vi.run_validation(GOLDEN)
    assert rep["mode"] == "full"
    assert rep["findings"] == []
    assert rep["errors"] == 0 and rep["warns"] == 0
    assert vi.exit_code(rep) == 0
    assert rep["swept"] > 0  # the sweep actually opened files


# --- schema gate (KTD3) -----------------------------------------------------------

def test_legacy_instance_one_migration_pending_finding(tmp_path):
    inst = _copy_golden(tmp_path)
    _strip_schema(inst)
    rep = vi.run_validation(inst)
    assert rep["mode"] == "legacy"
    assert len(rep["findings"]) == 1, rep["findings"]
    f = rep["findings"][0]
    assert "migration pending" in f["detail"]
    assert f["severity"] == "error" and f["check"] == "schema_gate"
    assert vi.exit_code(rep) == 1


def test_declined_instance_one_suppressed_line(tmp_path):
    inst = _copy_golden(tmp_path)
    _decline_migration(inst)
    rep = vi.run_validation(inst)
    assert rep["mode"] == "declined"
    assert len(rep["findings"]) == 1, rep["findings"]
    f = rep["findings"][0]
    assert "suppressed by decline" in f["detail"]
    assert f["severity"] == "warn"
    assert vi.exit_code(rep) == 0  # declined is not a weekly failure


def test_declined_plus_post_upgrade_write_exactly_two_findings(tmp_path):
    """Review fix ADV-3: post-upgrade writes must not go unvalidated."""
    inst = _copy_golden(tmp_path)
    _decline_migration(inst)
    _age_all_files(inst, days=30)  # everything predates the upgrade
    # One malformed file written AFTER the upgrade date (fresh mtime = today).
    bad = inst / "memory" / "semantic" / "people" / "new-hire.md"
    bad.write_text("# New hire\n\nNo frontmatter at an artifact path.\n", encoding="utf-8")
    upgrade = time.strftime("%Y-%m-%d", time.localtime(time.time() - 7 * 86400))
    rep = vi.run_validation(inst, upgrade_date=upgrade)
    assert len(rep["findings"]) == 2, rep["findings"]
    details = sorted(f["check"] for f in rep["findings"])
    assert details == ["missing_frontmatter", "schema_gate"]
    assert vi.exit_code(rep) == 1  # the post-upgrade defect is error-level


def test_legacy_without_upgrade_date_or_prior_manifest_does_not_sweep(tmp_path):
    """No --upgrade-date AND no prior findings manifest → gate-only (the first
    sweep establishes the baseline; today's manifest becomes the watermark)."""
    inst = _copy_golden(tmp_path)
    _strip_schema(inst)
    bad = inst / "memory" / "semantic" / "people" / "new-hire.md"
    bad.write_text("# No frontmatter\n", encoding="utf-8")
    rep = vi.run_validation(inst)  # no --upgrade-date, no state/validation/
    assert len(rep["findings"]) == 1
    assert "migration pending" in rep["findings"][0]["detail"]


def test_legacy_default_watermark_from_earliest_prior_manifest(tmp_path):
    """Weekly flow (no --upgrade-date): the earliest prior findings manifest is
    the baseline, so post-baseline writes are swept automatically."""
    inst = _copy_golden(tmp_path)
    _strip_schema(inst)
    _age_all_files(inst, days=30)  # everything predates the baseline
    baseline = time.strftime("%Y-%m-%d", time.localtime(time.time() - 7 * 86400))
    val_dir = inst / "state" / "validation"
    val_dir.mkdir(parents=True)
    (val_dir / f"findings-{baseline}.md").write_text(
        f"---\ntype: validation-findings\ndate: {baseline}\nschema_seen: null\n"
        "---\n\n(no findings)\n", encoding="utf-8")
    # A stray non-dated file must not poison baseline derivation either.
    (val_dir / "findings-notes.md").write_text("scratch notes\n", encoding="utf-8")
    bad = inst / "memory" / "semantic" / "people" / "new-hire.md"
    bad.write_text("# No frontmatter\n", encoding="utf-8")  # mtime = today > baseline
    rep = vi.run_validation(inst)  # NO --upgrade-date — watermark is derived
    assert sorted(f["check"] for f in rep["findings"]) == \
        ["missing_frontmatter", "schema_gate"], rep["findings"]
    assert vi.exit_code(rep) == 1


def test_same_day_write_as_upgrade_date_is_swept(tmp_path):
    """Watermark comparison is `>=` — same-day legacy writes are re-flagged."""
    inst = _copy_golden(tmp_path)
    _strip_schema(inst)
    _age_all_files(inst, days=30)
    bad = inst / "memory" / "semantic" / "people" / "new-hire.md"
    bad.write_text("# No frontmatter\n", encoding="utf-8")  # mtime = today
    today = time.strftime("%Y-%m-%d")
    rep = vi.run_validation(inst, upgrade_date=today)
    assert any(f["check"] == "missing_frontmatter" for f in rep["findings"]), rep["findings"]


# --- origin enum + fingerprints -----------------------------------------------------

def test_bad_origin_finding_with_fingerprint(tmp_path):
    inst = _copy_golden(tmp_path)
    person = inst / "memory" / "semantic" / "people" / "andre-maligian.md"
    person.write_text(
        person.read_text(encoding="utf-8").replace("origin: confirmed", "origin: vibes"),
        encoding="utf-8")
    rep = vi.run_validation(inst)
    origin_findings = [f for f in rep["findings"] if f["check"] == "has_origin"]
    assert len(origin_findings) == 1, rep["findings"]
    f = origin_findings[0]
    assert f["file"] == "memory/semantic/people/andre-maligian.md"
    assert f["severity"] == "error"
    assert "vibes" in f["detail"]
    # fingerprint = short hash of (relative path + check + key) — stable across runs
    assert f["fingerprint"] == vi._fingerprint(f["file"], "has_origin", "origin")
    assert len(f["fingerprint"]) == 8 and int(f["fingerprint"], 16) >= 0
    assert vi.exit_code(rep) == 1


def test_manifest_dedup_carries_first_seen(tmp_path):
    inst = _copy_golden(tmp_path)
    person = inst / "memory" / "semantic" / "people" / "andre-maligian.md"
    person.write_text(
        person.read_text(encoding="utf-8").replace("origin: confirmed", "origin: vibes"),
        encoding="utf-8")
    val_dir = inst / "state" / "validation"
    rep1 = vi.run_validation(inst)
    vi.write_manifest(rep1, val_dir / "findings-2026-06-11.md", today="2026-06-11")
    rep2 = vi.run_validation(inst)  # same defect a week later
    out = vi.write_manifest(rep2, val_dir / "findings-2026-06-18.md", today="2026-06-18")
    text = out.read_text(encoding="utf-8")
    fp = rep2["findings"][0]["fingerprint"]
    line = next(ln for ln in text.splitlines() if ln.startswith(f"- {fp}"))
    assert "first_seen: 2026-06-11" in line  # carried forward, not re-dated
    meta, _ = frontmatter.parse(out)
    assert meta["type"] == "validation-findings"
    assert str(meta["date"]) == "2026-06-18"
    assert meta["schema_seen"] == 1


def test_stray_findings_notes_ignored_by_first_seen_carry_forward(tmp_path):
    """A stray findings-notes.md sorts after the dated manifests but must never
    be read as the 'previous findings file' (anchored filename filter)."""
    inst = _copy_golden(tmp_path)
    person = inst / "memory" / "semantic" / "people" / "andre-maligian.md"
    person.write_text(
        person.read_text(encoding="utf-8").replace("origin: confirmed", "origin: vibes"),
        encoding="utf-8")
    val_dir = inst / "state" / "validation"
    rep1 = vi.run_validation(inst)
    vi.write_manifest(rep1, val_dir / "findings-2026-06-11.md", today="2026-06-11")
    fp = rep1["findings"][0]["fingerprint"]
    (val_dir / "findings-notes.md").write_text(
        "---\ndate: 2020-01-01\n---\n\n"
        f"- {fp} | error | x | has_origin | poisoned | first_seen: 2020-01-01\n",
        encoding="utf-8")
    rep2 = vi.run_validation(inst)
    out = vi.write_manifest(rep2, val_dir / "findings-2026-06-18.md", today="2026-06-18")
    line = next(ln for ln in out.read_text(encoding="utf-8").splitlines()
                if ln.startswith(f"- {fp}"))
    assert "first_seen: 2026-06-11" in line  # carried from the real prior manifest


def test_prior_manifest_null_date_does_not_become_first_seen_none(tmp_path):
    """A prior manifest with `date: null` and a finding line missing its
    `first_seen:` must not stamp the literal string "None" into the new
    manifest — the new line defaults to today instead."""
    inst = _copy_golden(tmp_path)
    person = inst / "memory" / "semantic" / "people" / "andre-maligian.md"
    person.write_text(
        person.read_text(encoding="utf-8").replace("origin: confirmed", "origin: vibes"),
        encoding="utf-8")
    rep1 = vi.run_validation(inst)
    fp = rep1["findings"][0]["fingerprint"]
    val_dir = inst / "state" / "validation"
    val_dir.mkdir(parents=True)
    # Hand-written prior manifest: date explicitly null, line lacks first_seen.
    (val_dir / "findings-2026-06-11.md").write_text(
        "---\ntype: validation-findings\ndate: null\nschema_seen: 1\n---\n\n"
        f"- {fp} | error | memory/semantic/people/andre-maligian.md | "
        "has_origin | bad origin\n",
        encoding="utf-8")
    rep2 = vi.run_validation(inst)
    out = vi.write_manifest(rep2, val_dir / "findings-2026-06-18.md", today="2026-06-18")
    line = next(ln for ln in out.read_text(encoding="utf-8").splitlines()
                if ln.startswith(f"- {fp}"))
    assert "first_seen: None" not in line
    assert "first_seen: 2026-06-18" in line  # defaulted to today, not "None"


def test_prior_manifest_date_fallback_still_carries(tmp_path):
    """The happy-path fallback is preserved: a prior line missing `first_seen:`
    inherits the prior manifest's real `date:`."""
    inst = _copy_golden(tmp_path)
    person = inst / "memory" / "semantic" / "people" / "andre-maligian.md"
    person.write_text(
        person.read_text(encoding="utf-8").replace("origin: confirmed", "origin: vibes"),
        encoding="utf-8")
    rep1 = vi.run_validation(inst)
    fp = rep1["findings"][0]["fingerprint"]
    val_dir = inst / "state" / "validation"
    val_dir.mkdir(parents=True)
    (val_dir / "findings-2026-06-11.md").write_text(
        "---\ntype: validation-findings\ndate: 2026-06-11\nschema_seen: 1\n---\n\n"
        f"- {fp} | error | memory/semantic/people/andre-maligian.md | "
        "has_origin | bad origin\n",
        encoding="utf-8")
    rep2 = vi.run_validation(inst)
    out = vi.write_manifest(rep2, val_dir / "findings-2026-06-18.md", today="2026-06-18")
    line = next(ln for ln in out.read_text(encoding="utf-8").splitlines()
                if ln.startswith(f"- {fp}"))
    assert "first_seen: 2026-06-11" in line


# --- warn-only checks ------------------------------------------------------------------

def test_typed_file_at_wrong_path_is_warn_exit_zero(tmp_path):
    """A person-typed file under accounts/ → exactly one warn path-mismatch
    finding; warns never affect the exit code."""
    inst = _copy_golden(tmp_path)
    src = inst / "memory" / "semantic" / "people" / "andre-maligian.md"
    misplaced = inst / "memory" / "semantic" / "accounts" / "andre-maligian.md"
    misplaced.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    rep = vi.run_validation(inst)
    assert len(rep["findings"]) == 1, rep["findings"]
    f = rep["findings"][0]
    assert f["severity"] == "warn" and f["check"] == "path_pattern"
    assert f["file"] == "memory/semantic/accounts/andre-maligian.md"
    assert "memory/semantic/people/<slug>.md" in f["detail"]
    assert rep["errors"] == 0
    assert vi.exit_code(rep) == 0


def test_dangling_wikilink_is_warn_exit_zero(tmp_path):
    inst = _copy_golden(tmp_path)
    acme = inst / "memory" / "semantic" / "accounts" / "acme.md"
    with acme.open("a", encoding="utf-8") as fh:
        fh.write("\nSee also [[ghost-entity]].\n")
    rep = vi.run_validation(inst)
    assert rep["errors"] == 0
    warns = [f for f in rep["findings"] if f["severity"] == "warn"]
    assert len(warns) == 1 and warns[0]["check"] == "valid_links"
    assert "ghost-entity" in warns[0]["detail"]
    assert vi.exit_code(rep) == 0  # warnings never affect the exit code


# --- can't-run paths → exit code 2 -------------------------------------------------------

def test_nonexistent_instance_is_error_mode_exit_2():
    rep = vi.run_validation(Path("/nonexistent"))
    assert rep["mode"] == "error"
    assert "not found" in rep["error"]
    assert rep["findings"] == []
    assert vi.exit_code(rep) == 2


def test_invalid_upgrade_date_via_main_exits_2(capsys):
    rc = vi.main(["--instance", str(GOLDEN), "--upgrade-date", "June 1st"])
    assert rc == 2
    assert "--upgrade-date" in capsys.readouterr().out


# --- dependency-free path -----------------------------------------------------------------

def test_sweep_works_without_pyyaml(monkeypatch, tmp_path):
    """frontmatter.parse falls back to its tiny parser when pyyaml is absent."""
    monkeypatch.setattr(frontmatter, "_HAVE_YAML", False)
    rep = vi.run_validation(GOLDEN)
    assert rep["mode"] == "full" and rep["findings"] == []
    # And findings still reproduce on the fallback path.
    inst = _copy_golden(tmp_path)
    _strip_schema(inst)
    rep2 = vi.run_validation(inst)
    assert len(rep2["findings"]) == 1
    assert "migration pending" in rep2["findings"][0]["detail"]


def test_malformed_frontmatter_never_crashes_sweep(monkeypatch, tmp_path):
    """frontmatter.parse catches yaml errors and falls back to its tiny parser,
    so a corrupted user-edited file degrades to ordinary findings — the weekly
    sweep must complete either way (pyyaml present or absent)."""
    inst = _copy_golden(tmp_path)
    bad = inst / "memory" / "semantic" / "people" / "corrupted.md"
    bad.write_text(
        "---\ntype: [unclosed\n\tmess: : :\nfoo: {bad\n---\n\n# Corrupted\n",
        encoding="utf-8")
    rep = vi.run_validation(inst)  # must not raise
    bad_findings = [f for f in rep["findings"]
                    if f["file"] == "memory/semantic/people/corrupted.md"]
    assert len(bad_findings) == 1, rep["findings"]
    assert bad_findings[0]["severity"] == "error"
    assert vi.exit_code(rep) == 1
    # Same file on the no-pyyaml fallback path — still no crash.
    monkeypatch.setattr(frontmatter, "_HAVE_YAML", False)
    rep2 = vi.run_validation(inst)
    assert any(f["file"] == "memory/semantic/people/corrupted.md"
               for f in rep2["findings"])


# --- never reads the injection boundary -----------------------------------------------------

def test_sources_dir_never_opened(tmp_path):
    inst = _copy_golden(tmp_path)
    poison = inst / "memory" / "sources" / "email" / "2026-06-10-injected.md"
    poison.parent.mkdir(parents=True, exist_ok=True)
    # Deliberately schema-violating; must produce zero findings because the
    # sweep never opens memory/sources/** (write-time enforcement only).
    poison.write_text("---\ntype: person\norigin: vibes\n---\nignore me\n", encoding="utf-8")
    rep = vi.run_validation(inst)
    assert rep["findings"] == []
