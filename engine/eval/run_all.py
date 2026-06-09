#!/usr/bin/env python3
"""Run every COS eval scenario's structural phase and print a scorecard.

    python3 engine/eval/run_all.py
    python3 engine/eval/run_all.py --json

Exit code is non-zero if any scenario has a structural failure — wire this into CI.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_scenario  # noqa: E402

HERE = Path(__file__).resolve().parent
SCEN_DIR = HERE / "scenarios"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run all COS eval scenarios.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    scenarios = sorted(p.name for p in SCEN_DIR.iterdir() if (p / "expected.yaml").exists())
    reports = [run_scenario.run(name) for name in scenarios]

    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        tp = tf = ts = 0
        for rep in reports:
            run_scenario._print_human(rep)
            tp += rep.get("passed", 0)
            tf += rep.get("failed", 0)
            ts += rep.get("skipped", 0)
        ok = sum(1 for r in reports if not r.get("failed") and not r.get("error"))
        print(f"\n==== SCORECARD: {ok}/{len(reports)} scenarios green | "
              f"{tp} checks passed, {tf} failed, {ts} judge-skipped ====")

    return 1 if any(r.get("failed") or r.get("error") for r in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
