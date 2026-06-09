#!/usr/bin/env python3
"""Run one COS eval scenario's structural phase against an instance directory.

A scenario is a *longitudinal* fixture: ordered weekly inputs under `turns/`
plus a `golden/` end-state snapshot of the instance a correct run should
produce. The structural phase (this runner) asserts invariants against an
instance dir — by default the golden snapshot, so the harness self-tests; or a
real run's output via --instance.

    run_scenario.py 01-write-back-loop                  # validate golden/ (self-test)
    run_scenario.py 01-write-back-loop --instance ./out # validate a real run
    run_scenario.py 01-write-back-loop --json

Content (LLM-as-judge) assertions are declared with a `judge:` key and SKIPPED
here — they belong to the optional content phase, not the deterministic one.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import assertions  # noqa: E402

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

HERE = Path(__file__).resolve().parent
SCEN_DIR = HERE / "scenarios"

_GLYPH = {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}


def _load_expected(scenario_dir: Path) -> dict:
    if yaml is None:
        sys.exit("ERROR: pyyaml required — pip install -r engine/eval/requirements.txt")
    return yaml.safe_load((scenario_dir / "expected.yaml").read_text(encoding="utf-8")) or {}


def run(scenario: str, instance: Path | None = None) -> dict:
    scenario_dir = Path(scenario) if Path(scenario).is_dir() else SCEN_DIR / scenario
    if not scenario_dir.is_dir():
        return {"scenario": scenario, "error": f"scenario not found: {scenario_dir}", "failed": 1, "passed": 0, "skipped": 0, "results": []}
    spec = _load_expected(scenario_dir)
    inst = instance or (scenario_dir / "golden")
    results = []
    passed = failed = skipped = 0
    for item in spec.get("final", []):
        desc = item.get("desc", "")
        if assertions.JUDGE in item:
            skipped += 1
            results.append({"status": "skip", "desc": desc, "detail": "judge (content phase / --judge)"})
            continue
        check_name = next((k for k in item if k in assertions.CHECKS), None)
        if check_name is None:
            failed += 1
            results.append({"status": "fail", "desc": desc, "detail": f"unknown check in {list(item)}"})
            continue
        ok, detail = assertions.CHECKS[check_name](inst, item[check_name])
        results.append({"status": "pass" if ok else "fail", "desc": desc, "detail": detail})
        passed += ok
        failed += not ok
    return {
        "scenario": scenario_dir.name,
        "instance": str(inst),
        "turns": [t.get("name", t) if isinstance(t, dict) else t for t in spec.get("turns", [])],
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "results": results,
    }


def _print_human(rep: dict) -> None:
    if rep.get("error"):
        print(f"ERROR [{rep['scenario']}]: {rep['error']}")
        return
    print(f"\n=== {rep['scenario']}  (instance: {rep['instance']}) ===")
    if rep["turns"]:
        print("turns: " + " → ".join(str(t) for t in rep["turns"]))
    for r in rep["results"]:
        line = f"  [{_GLYPH[r['status']]}] {r['detail']}"
        if r["desc"]:
            line += f"   — {r['desc']}"
        print(line)
    print(f"  ---- {rep['passed']} passed, {rep['failed']} failed, {rep['skipped']} skipped (judge)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run a COS eval scenario (structural phase).")
    ap.add_argument("scenario", help="scenario name under engine/eval/scenarios/ or a path")
    ap.add_argument("--instance", type=Path, default=None, help="instance dir to validate (default: scenario golden/)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of human output")
    args = ap.parse_args(argv)
    rep = run(args.scenario, args.instance)
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        _print_human(rep)
    return 1 if rep.get("failed") or rep.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
