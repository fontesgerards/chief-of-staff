#!/usr/bin/env python3
"""cos-validate — deterministic instance validation sweep (plan U8, R12, KTD3, KTD7).

Production tooling (not eval harness): invoked weekly by `cos-system-maintenance`,
findings consumed by the next `cos-consolidate-memory` run. Stdlib-only — works
without pyyaml via frontmatter.py's fallback parser.

    python3 engine/validate_instance.py --instance <path> \
        [--manifest <out.md>] [--upgrade-date YYYY-MM-DD]

Behavior:
- Schema gate (KTD3): `config.md` frontmatter `schema:` missing or < 1 → exactly
  ONE "migration pending" finding for the legacy remainder (never hundreds);
  `migration: declined` → one "suppressed by decline" line instead. In both
  cases files written AFTER `--upgrade-date` (git-add date or mtime) are still
  swept — post-upgrade writes must not go unvalidated (review fix ADV-3).
- Sweep: every instance `*.md` minus schema.SWEEP_EXCLUSIONS (`memory/sources/**`
  is the injection boundary — never opened) and router files (CLAUDE.md/AGENTS.md).
  Typed artifacts are checked for required_keys + valid `origin`; `valid_links`
  is warn-only (schema.WARN_ONLY_CHECKS) and never affects the exit code.
- Manifest: `--manifest` writes the findings file (the skill passes
  `state/validation/findings-<date>.md`); fingerprints dedup against the
  previous findings file in the same dir by carrying `first_seen:` forward.
- Exit codes: 0 = no error-level findings; 1 = error findings; 2 = can't run.

The sweep NEVER edits memory — it only reads and reports.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import re
import subprocess
import sys
from pathlib import Path

# sys.path shim mirroring engine/eval/conftest.py — the rules live in engine/eval/lib.
sys.path.insert(0, str(Path(__file__).resolve().parent / "eval"))
from lib import assertions, frontmatter, schema  # noqa: E402

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
FINDING_LINE = re.compile(r"^- ([0-9a-f]{8,}) \|")
FIRST_SEEN = re.compile(r"first_seen: (\d{4}-\d{2}-\d{2})")

# Memory routers / entry files — structural, not artifacts; never carry a type schema.
ROUTER_BASENAMES = {"CLAUDE.md", "AGENTS.md"}


# --- pattern compilation (from schema.py's data) ------------------------------

def _glob_to_regex(glob: str) -> re.Pattern:
    """Translate a SWEEP_EXCLUSIONS glob (`**` crosses `/`, `*` does not)."""
    out, i = [], 0
    while i < len(glob):
        if glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif glob[i] == "*":
            out.append("[^/]*")
            i += 1
        else:
            out.append(re.escape(glob[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def _path_pattern_to_regex(pattern: str) -> re.Pattern:
    """Translate an ARTIFACT_TYPES path_pattern (`<slug>`, `YYYY-MM-DD`, `YYYY-MM`)."""
    SLUG, DAY, MONTH = "\x00", "\x01", "\x02"
    p = re.sub(r"<[^>]+>", SLUG, pattern)
    p = p.replace("YYYY-MM-DD", DAY).replace("YYYY-MM", MONTH)
    p = re.escape(p)
    p = p.replace(SLUG, r"[^/]+").replace(DAY, r"\d{4}-\d{2}-\d{2}").replace(MONTH, r"\d{4}-\d{2}")
    return re.compile("^" + p + "$")


EXCLUSION_RX = [_glob_to_regex(g) for g in schema.SWEEP_EXCLUSIONS]
ARTIFACT_PATH_RX = [
    (typ, _path_pattern_to_regex(spec["path_pattern"]))
    for typ, spec in schema.ARTIFACT_TYPES.items()
]


# --- findings ------------------------------------------------------------------

def _fingerprint(rel: str, check: str, key: str) -> str:
    """Stable short id of (relative path + check + key) — dedup unit across runs."""
    return hashlib.sha1(f"{rel}|{check}|{key}".encode("utf-8")).hexdigest()[:8]


def _finding(severity: str, rel: str, check: str, key: str, detail: str) -> dict:
    return {
        "fingerprint": _fingerprint(rel, check, key),
        "severity": severity,
        "file": rel,
        "check": check,
        "key": key,
        "detail": detail,
    }


# --- sweep ----------------------------------------------------------------------

def iter_sweep_files(instance: Path):
    """Yield (rel, path) for every instance markdown file the sweep may open."""
    for p in sorted(instance.rglob("*.md")):
        if p.name in ROUTER_BASENAMES:
            continue
        rel = p.relative_to(instance).as_posix()
        if any(rx.match(rel) for rx in EXCLUSION_RX):
            continue
        yield rel, p


def check_file(instance: Path, rel: str) -> list[dict]:
    """Deterministic checks for one swept file. Reuses assertions.py per-path checks."""
    meta, _ = frontmatter.parse(instance / rel)
    typ = meta.get("type")
    spec = schema.ARTIFACT_TYPES.get(str(typ)) if typ else None
    findings: list[dict] = []
    if spec is None:
        # No recognized type: a finding only when the path claims to be an artifact.
        for typ_name, rx in ARTIFACT_PATH_RX:
            if rx.match(rel):
                findings.append(_finding(
                    "error", rel, "missing_frontmatter", "type",
                    f"no recognized `type:` frontmatter but path matches the "
                    f"'{typ_name}' artifact pattern",
                ))
                break
        return findings
    for key in spec["required_keys"]:
        if key not in meta:
            findings.append(_finding(
                "error", rel, "required_keys", key,
                f"missing required frontmatter key '{key}' (type: {typ})",
            ))
    if "origin" in meta:  # a MISSING origin is already a required_keys finding
        ok, detail = assertions.has_origin(instance, rel)
        if not ok:
            findings.append(_finding("error", rel, "has_origin", "origin", detail))
    ok, detail = assertions.valid_links(instance, rel)
    if not ok:
        severity = "warn" if "valid_links" in schema.WARN_ONLY_CHECKS else "error"
        findings.append(_finding(severity, rel, "valid_links", "links", detail))
    return findings


def _file_date(instance: Path, rel: str, path: Path) -> str:
    """Latest of git-add date and mtime (ISO) — 'written after upgrade' detector.
    Git is best-effort; tmp fixtures and git-less hosts fall back to mtime."""
    mtime = datetime.date.fromtimestamp(path.stat().st_mtime).isoformat()
    try:
        out = subprocess.run(
            ["git", "-C", str(instance), "log", "--diff-filter=A",
             "--format=%as", "-1", "--", rel],
            capture_output=True, text=True, timeout=10,
        )
        added = out.stdout.strip().splitlines()[-1] if out.returncode == 0 and out.stdout.strip() else ""
        if DATE_RE.fullmatch(added):
            return max(added, mtime)
    except Exception:
        pass
    return mtime


def run_validation(instance: Path, upgrade_date: str | None = None) -> dict:
    """Run the sweep; returns a report dict (findings, counts, mode). Pure read."""
    instance = Path(instance)
    if not instance.is_dir():
        return {"instance": str(instance), "mode": "error", "schema_seen": None,
                "error": f"instance dir not found: {instance}",
                "findings": [], "errors": 0, "warns": 0, "swept": 0}
    cfg_path = instance / "config.md"
    cfg, _ = frontmatter.parse(cfg_path) if cfg_path.is_file() else ({}, "")
    schema_seen = cfg.get("schema")
    migrated = (isinstance(schema_seen, int) and not isinstance(schema_seen, bool)
                and schema_seen >= 1)
    declined = str(cfg.get("migration", "")).strip().lower() == "declined"

    findings: list[dict] = []
    swept = 0
    if migrated:
        mode = "full"
        for rel, _p in iter_sweep_files(instance):
            swept += 1
            findings.extend(check_file(instance, rel))
    else:
        # Schema gate (KTD3): one line for the legacy remainder, not hundreds.
        if declined:
            mode = "declined"
            findings.append(_finding(
                "warn", "config.md", "schema_gate", "migration",
                "suppressed by decline — legacy remainder not swept "
                "(config.md `migration: declined`)",
            ))
        else:
            mode = "legacy"
            findings.append(_finding(
                "error", "config.md", "schema_gate", "schema",
                "migration pending — legacy remainder not swept "
                "(config.md `schema:` missing or < 1)",
            ))
        # Review fix ADV-3: post-upgrade writes must not go unvalidated.
        if upgrade_date:
            for rel, p in iter_sweep_files(instance):
                if _file_date(instance, rel, p) > upgrade_date:
                    swept += 1
                    findings.extend(check_file(instance, rel))

    errors = sum(1 for f in findings if f["severity"] == "error")
    warns = sum(1 for f in findings if f["severity"] == "warn")
    return {"instance": str(instance), "mode": mode, "schema_seen": schema_seen,
            "findings": findings, "errors": errors, "warns": warns, "swept": swept}


# --- findings manifest (KTD7) ----------------------------------------------------

def _previous_first_seen(manifest_path: Path) -> dict:
    """fingerprint → first_seen date from the latest prior findings file in the dir."""
    prev = sorted(p for p in manifest_path.parent.glob("findings-*.md")
                  if p.resolve() != manifest_path.resolve())
    if not prev:
        return {}
    latest = prev[-1]
    meta, body = frontmatter.parse(latest)
    fallback = str(meta.get("date", "")) or None
    out = {}
    for line in body.splitlines():
        m = FINDING_LINE.match(line.strip())
        if not m:
            continue
        seen = FIRST_SEEN.search(line)
        out[m.group(1)] = seen.group(1) if seen else fallback
    return out


def write_manifest(report: dict, manifest_path: Path, today: str | None = None) -> Path:
    """Write the findings manifest; dedup by carrying first_seen per fingerprint."""
    manifest_path = Path(manifest_path)
    today = today or datetime.date.today().isoformat()
    prior = _previous_first_seen(manifest_path)
    schema_seen = report.get("schema_seen")
    lines = [
        "---",
        "type: validation-findings",
        f"date: {today}",
        f"schema_seen: {schema_seen if schema_seen is not None else 'null'}",
        "---",
        "",
        f"# Validation findings — {today}",
        "",
        f"Instance: `{report['instance']}` · mode: {report['mode']} · "
        f"{report['errors']} error(s), {report['warns']} warn(s), "
        f"{report['swept']} file(s) swept.",
        "",
    ]
    if report["findings"]:
        for f in report["findings"]:
            first_seen = prior.get(f["fingerprint"], today)
            lines.append(
                f"- {f['fingerprint']} | {f['severity']} | {f['file']} | "
                f"{f['check']} | {f['detail']} | first_seen: {first_seen}"
            )
    else:
        lines.append("(no findings)")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest_path


# --- CLI --------------------------------------------------------------------------

def exit_code(report: dict) -> int:
    if report.get("error"):
        return 2
    return 1 if report["errors"] else 0


def _print_summary(report: dict) -> None:
    if report.get("error"):
        print(f"ERROR: {report['error']}")
        return
    print(f"cos-validate — {report['instance']}")
    print(f"mode: {report['mode']} (schema: {report['schema_seen']!r}) · "
          f"{report['swept']} file(s) swept")
    for f in report["findings"]:
        print(f"  [{f['severity'].upper():5}] {f['file']} · {f['check']} · {f['detail']}")
    if not report["findings"]:
        print("  OK — no findings")
    print(f"---- {report['errors']} error(s), {report['warns']} warn(s)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Deterministic COS instance validation sweep (read-only).")
    ap.add_argument("--instance", type=Path, required=True,
                    help="instance directory to validate")
    ap.add_argument("--manifest", type=Path, default=None,
                    help="write the findings manifest here "
                         "(e.g. <instance>/state/validation/findings-<date>.md)")
    ap.add_argument("--upgrade-date", default=None, metavar="YYYY-MM-DD",
                    help="on legacy/declined instances, still sweep files written "
                         "after this date (git-add date or mtime)")
    args = ap.parse_args(argv)

    if args.upgrade_date and not DATE_RE.fullmatch(args.upgrade_date):
        print(f"ERROR: --upgrade-date must be YYYY-MM-DD, got {args.upgrade_date!r}")
        return 2

    report = run_validation(args.instance, upgrade_date=args.upgrade_date)
    _print_summary(report)
    if args.manifest and not report.get("error"):
        path = write_manifest(report, args.manifest)
        print(f"manifest: {path}")
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
