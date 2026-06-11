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


def test_legacy_without_upgrade_date_does_not_sweep(tmp_path):
    inst = _copy_golden(tmp_path)
    _strip_schema(inst)
    bad = inst / "memory" / "semantic" / "people" / "new-hire.md"
    bad.write_text("# No frontmatter\n", encoding="utf-8")
    rep = vi.run_validation(inst)  # no --upgrade-date
    assert len(rep["findings"]) == 1
    assert "migration pending" in rep["findings"][0]["detail"]


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


# --- warn-only checks ------------------------------------------------------------------

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
