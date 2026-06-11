"""Repo-level CI lockstep guards (plan U3, R15). Stdlib-only.

Two invariants the release process must never drift on:

1. **Manifest version equality** — the four versioned plugin manifests
   (claude / codex / cursor plugin.json + the cursor marketplace's
   `metadata.version`) must agree. Root `.claude-plugin/marketplace.json`
   carries no version field — excluded by design.

2. **Root mirror** — root `CLAUDE.md` and `AGENTS.md` are the same document
   for two runtimes. They must be equal after normalizing the three
   documented, tolerated deltas (review finding F-2).

`run_guards()` returns a report shaped like a scenario report so
`run_all.py` can print it alongside the scenario scorecard and fold it into
the exit code. The individual checks are importable so tests never shell out.
"""
from __future__ import annotations

from pathlib import Path
import json

# engine/eval/lib/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[3]

# (repo-relative path, key path to the version string)
MANIFESTS = [
    ("engine/.claude-plugin/plugin.json", ("version",)),
    ("engine/.codex-plugin/plugin.json", ("version",)),
    ("engine/.cursor-plugin/plugin.json", ("version",)),
    (".cursor-plugin/marketplace.json", ("metadata", "version")),
]


def check_manifest_versions(root: Path = REPO_ROOT):
    """All four versioned manifests carry the same version string."""
    versions: dict[str, str] = {}
    for rel, keypath in MANIFESTS:
        path = root / rel
        if not path.is_file():
            return False, f"{rel} MISSING"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return False, f"{rel} unparseable: {exc}"
        val = data
        for key in keypath:
            val = val.get(key) if isinstance(val, dict) else None
        if not isinstance(val, str) or not val.strip():
            return False, f"{rel} has no {'.'.join(keypath)} string"
        versions[rel] = val.strip()
    distinct = sorted(set(versions.values()))
    if len(distinct) == 1:
        return True, f"all {len(MANIFESTS)} manifests at version {distinct[0]}"
    return False, "version mismatch: " + ", ".join(f"{rel}={v}" for rel, v in versions.items())


def normalize_mirror(text: str) -> str:
    """Erase the tolerated CLAUDE.md/AGENTS.md deltas (review finding F-2 — three):
    after normalization the two files must be byte-equal."""
    # 1. Codex invokes skills with a `$` prefix where Claude Code uses `/`
    #    (both the literal skill names and the `<name>` placeholder).
    text = text.replace("$cos-", "/cos-").replace("`$<name>`", "`/<name>`")
    # 2. AGENTS.md says the file is "loaded automatically by Codex".
    text = text.replace(" by Codex", "")
    # 3. AGENTS.md additionally mentions the `/skills` menu as an invocation path.
    text = text.replace(", or via the `/skills` menu", "")
    return text


def check_root_mirror(root: Path = REPO_ROOT):
    """Root CLAUDE.md and AGENTS.md are mirrors modulo the tolerated deltas."""
    paths = [root / "CLAUDE.md", root / "AGENTS.md"]
    for p in paths:
        if not p.is_file():
            return False, f"{p.name} MISSING at repo root"
    a, b = (normalize_mirror(p.read_text(encoding="utf-8")) for p in paths)
    if a == b:
        return True, "CLAUDE.md ≡ AGENTS.md (modulo the 3 tolerated deltas)"
    a_lines, b_lines = a.splitlines(), b.splitlines()
    for i, (la, lb) in enumerate(zip(a_lines, b_lines), 1):
        if la != lb:
            return False, (f"diverge at line {i}: CLAUDE.md {la!r} vs AGENTS.md {lb!r}")
    return False, (f"diverge in length after normalization: "
                   f"CLAUDE.md {len(a_lines)} lines vs AGENTS.md {len(b_lines)} lines")


GUARDS = [
    ("manifest versions move in lockstep", check_manifest_versions),
    ("root CLAUDE.md mirrors AGENTS.md", check_root_mirror),
]


def run_guards(root: Path = REPO_ROOT) -> dict:
    """Run every guard; report shaped like run_scenario.run() for the scorecard."""
    results = []
    passed = failed = 0
    for desc, fn in GUARDS:
        ok, detail = fn(root)
        results.append({"status": "pass" if ok else "fail", "desc": desc, "detail": detail})
        passed += ok
        failed += not ok
    return {
        "scenario": "repo-guards",
        "instance": str(root),
        "turns": [],
        "passed": passed,
        "failed": failed,
        "skipped": 0,
        "results": results,
    }
