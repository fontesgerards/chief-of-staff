#!/usr/bin/env bash
# Wire the AI Chief of Staff skills into Claude Code and Codex.
# Canonical skills live in engine/skills/. This points each runtime's skills
# directory at them, so /onboarding (Claude) and $onboarding (Codex) just work.
#
# Usage:
#   ./setup.sh           # symlink (one source of truth — recommended)
#   ./setup.sh --copy    # copy instead of symlink (Windows / if your runtime won't follow symlinks)
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-symlink}"

wire() {  # $1 = runtime dir (.claude or .agents)
  local dir="$1"
  mkdir -p "$dir"
  rm -rf "$dir/skills"
  if [ "$MODE" = "--copy" ]; then
    cp -R engine/skills "$dir/skills"
    echo "  copied  engine/skills → $dir/skills"
  else
    ln -s ../engine/skills "$dir/skills"
    echo "  linked  $dir/skills → engine/skills"
  fi
}

echo "Wiring skills…"
wire ".claude"   # Claude Code / Code tab  → /onboarding
wire ".agents"   # Codex                   → \$onboarding or /skills

echo ""
echo "Done. Open this folder in your runtime and run:"
echo "  Claude Code:  /onboarding"
echo "  Codex:        \$onboarding   (or pick it from /skills)"
echo ""
echo "If skills don't appear, re-run with --copy and restart the runtime."
