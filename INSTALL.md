# Install — make the skills invocable

The skills are authored once in `engine/skills/<name>/SKILL.md` and exposed to both runtimes. One command wires them up.

## Quick start

```bash
cd "AI Chief Of Staff"
./setup.sh            # symlinks engine/skills into .claude/ and .agents/
```

Then open this folder in your runtime and run **onboarding first**:

| Runtime | Invoke |
|---|---|
| **Claude Code** (CLI or the Code tab in the desktop app) | `/onboarding` — then `/meeting-prep`, `/loop-closing`, … |
| **Codex** (CLI) | `$onboarding` — or open the `/skills` menu and pick it |

> **Note on Codex syntax:** Codex uses `$skill-name` (not `/skill-name`); the old slash-prompt system is deprecated. The `/skills` menu lists everything by description.

## Zero-install (cloning)

`.claude/skills` and `.agents/skills` are committed as symlinks, so on macOS / Linux / WSL a fresh clone already works — `setup.sh` is only needed if you moved the folder or your runtime doesn't follow symlinked skill dirs.

## If skills don't show up

```bash
./setup.sh --copy     # copies instead of symlinking, then restart the runtime
```

Use `--copy` on native Windows or any runtime that won't traverse a symlinked `skills/` directory. (Trade-off: copies drift from `engine/skills/` — re-run after editing a skill.)

## What gets wired

- `.claude/skills → engine/skills` (Claude discovers `/<name>`)
- `.agents/skills → engine/skills` (Codex discovers `$<name>` / `/skills`)
- Always-loaded behavior comes from `CLAUDE.md` (Claude) and `AGENTS.md` (Codex) at the repo root, which point at `engine/INSTRUCTIONS.md`.

## Scheduled skills

`consolidate-memory`, `meeting-prep`, etc. also run on the cadences in `instance/config.md` (`schedules:`). If your runtime can't schedule natively, an external `cron`/`launchd` job reads the same block — see `engine/docs/U0-capability-spike.md` (a).
