"""Tests for the repo-level CI lockstep guards (plan U3, R15).

The guard logic is importable (lib/repo_guards.py) so these never shell out;
fixture repos are built in tmp_path.
"""
from __future__ import annotations

import json
from pathlib import Path

from lib import repo_guards


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_repo(root: Path, versions: dict[str, str] | None = None) -> Path:
    """Minimal fixture repo with the four manifests + mirrored root docs."""
    versions = versions or {}

    def v(rel: str) -> str:
        return versions.get(rel, "0.5.0")

    for rel in ("engine/.claude-plugin/plugin.json",
                "engine/.codex-plugin/plugin.json",
                "engine/.cursor-plugin/plugin.json"):
        _write(root / rel, json.dumps({"name": "chief-of-staff-plugin", "version": v(rel)}))
    _write(root / ".cursor-plugin/marketplace.json",
           json.dumps({"name": "chief-of-staff-plugin",
                       "metadata": {"version": v(".cursor-plugin/marketplace.json")}}))
    # Mirrored root docs differing only by the three tolerated deltas.
    _write(root / "CLAUDE.md",
           "# COS\n\nLoaded automatically — the index.\n"
           "Skills are invocable as `/<name>` (e.g. `/cos-onboarding`). Run `/cos-onboarding` first.\n")
    _write(root / "AGENTS.md",
           "# COS\n\nLoaded automatically by Codex — the index.\n"
           "Skills are invocable as `$<name>` (e.g. `$cos-onboarding`), or via the `/skills` menu. "
           "Run `$cos-onboarding` first.\n")
    return root


# --- manifest version equality ------------------------------------------------

def test_versions_in_lockstep_pass(tmp_path):
    ok, detail = repo_guards.check_manifest_versions(_make_repo(tmp_path))
    assert ok, detail
    assert "0.5.0" in detail


def test_single_bumped_manifest_fails(tmp_path):
    root = _make_repo(tmp_path, versions={"engine/.claude-plugin/plugin.json": "0.6.0"})
    ok, detail = repo_guards.check_manifest_versions(root)
    assert not ok
    assert "0.6.0" in detail and "0.5.0" in detail


def test_marketplace_metadata_version_is_read(tmp_path):
    root = _make_repo(tmp_path, versions={".cursor-plugin/marketplace.json": "9.9.9"})
    ok, detail = repo_guards.check_manifest_versions(root)
    assert not ok
    assert "9.9.9" in detail


def test_missing_manifest_fails(tmp_path):
    root = _make_repo(tmp_path)
    (root / "engine/.codex-plugin/plugin.json").unlink()
    ok, detail = repo_guards.check_manifest_versions(root)
    assert not ok
    assert "MISSING" in detail


def test_missing_version_key_fails(tmp_path):
    root = _make_repo(tmp_path)
    _write(root / ".cursor-plugin/marketplace.json", json.dumps({"metadata": {}}))
    ok, detail = repo_guards.check_manifest_versions(root)
    assert not ok
    assert "metadata.version" in detail


def test_invalid_json_fails(tmp_path):
    root = _make_repo(tmp_path)
    _write(root / "engine/.cursor-plugin/plugin.json", "{not json")
    ok, detail = repo_guards.check_manifest_versions(root)
    assert not ok
    assert "unparseable" in detail


# --- root mirror ----------------------------------------------------------------

def test_mirror_with_only_tolerated_deltas_passes(tmp_path):
    ok, detail = repo_guards.check_root_mirror(_make_repo(tmp_path))
    assert ok, detail


def test_divergence_beyond_tolerance_fails(tmp_path):
    root = _make_repo(tmp_path)
    claude = root / "CLAUDE.md"
    claude.write_text(claude.read_text(encoding="utf-8")
                      + "\nA new skill listed only here.\n", encoding="utf-8")
    ok, detail = repo_guards.check_root_mirror(root)
    assert not ok
    assert "diverge" in detail


def test_in_line_divergence_reports_line(tmp_path):
    root = _make_repo(tmp_path)
    agents = root / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8")
                      .replace("the index", "the encyclopedia"), encoding="utf-8")
    ok, detail = repo_guards.check_root_mirror(root)
    assert not ok
    assert "line 3" in detail


def test_missing_mirror_file_fails(tmp_path):
    root = _make_repo(tmp_path)
    (root / "AGENTS.md").unlink()
    ok, detail = repo_guards.check_root_mirror(root)
    assert not ok
    assert "AGENTS.md MISSING" in detail


# --- the guards hold on the CURRENT repo (green at introduction) -----------------

def test_current_repo_versions_in_lockstep():
    ok, detail = repo_guards.check_manifest_versions()
    assert ok, detail


def test_current_repo_mirror_holds():
    ok, detail = repo_guards.check_root_mirror()
    assert ok, detail


# --- report shape consumed by run_all.py -----------------------------------------

def test_run_guards_report_shape(tmp_path):
    rep = repo_guards.run_guards(_make_repo(tmp_path))
    assert rep["scenario"] == "repo-guards"
    assert rep["failed"] == 0 and rep["passed"] == len(repo_guards.GUARDS)
    assert {r["status"] for r in rep["results"]} == {"pass"}


def test_run_guards_flags_failures(tmp_path):
    root = _make_repo(tmp_path, versions={"engine/.claude-plugin/plugin.json": "0.6.0"})
    rep = repo_guards.run_guards(root)
    assert rep["failed"] == 1
