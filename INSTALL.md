# Install

Three paths. Each is self-contained — read yours top to bottom and ignore the others.

| You are using… | Your path |
|---|---|
| **Claude Cowork** (desktop app, no terminal) | [Path 1](#path-1--claude-cowork-no-terminal) |
| **Claude Code** (CLI or the Code tab) | [Path 2](#path-2--claude-code-cli) |
| A **git clone** (dev work, or no plugin) | [Path 3](#path-3--clone-dev--no-plugin) |

Whatever the path, the **engine** (skills, methods, templates) is shared and identical for everyone; your **instance** (private brain) is created by `/cos-onboarding` in a folder you confirm. Connector questions of any kind: `engine/methods/connectors.md`.

---

## Path 1 — Claude Cowork (no terminal)

1. **Install the plugin:** **Customize → Plugins → Browse plugins** → find **chief-of-staff** (marketplace `fontesgerards/chief-of-staff`) → Install. Skills appear as slash commands (`/cos-onboarding`, `/cos-meeting-prep`, …).
2. **Open (or create) the folder** where you want your brain to live, and make it the session's working folder.
3. **Run `/cos-onboarding`.** It runs a preflight first (`cos-preflight`) that probes — rather than assumes — what Cowork supports, and records the result in your `config.md`. Two things it will be honest with you about:
   - **Schedules expire.** Cowork scheduled tasks last ~7 days and run only while the app is open. The preflight records that; your config never claims "set-and-forget" where it isn't, and overdue schedules surface a re-arm prompt.
   - **The outbound-gate hook doesn't fire on Cowork** ([anthropics/claude-code#63360](https://github.com/anthropics/claude-code/issues/63360)), so the structural send-gate is degraded there. The fallback floor: connect every connector **read-only at the OAuth consent screen** where offered. The system still proposes-never-acts by instruction; it just can't enforce it structurally on this runtime.
4. **Wire connectors** (two different places — this trips people up):
   - **Gmail / Calendar / Drive** (and Microsoft 365): Anthropic **built-in** connectors — **Customize → Connectors → Connect**. They are *not* in the plugin's tab.
   - **Granola / Zoom / Fathom / Fireflies / Slack:** the chief-of-staff **plugin's own Connectors tab** → Connect → OAuth (prefer read-only).
5. **After plugin updates:** re-sync/update the plugin from the marketplace — new or changed connectors don't appear in the tab until you do.

> **`setup.sh` is NOT part of this path.** It belongs to the clone path only — don't mix it with a marketplace install (you'd end up with two copies of the skills).

---

## Path 2 — Claude Code (CLI)

1. **Install the plugin:**

   ```text
   /plugin marketplace add fontesgerards/chief-of-staff
   /plugin install chief-of-staff@chief-of-staff
   ```

2. **Run `/cos-onboarding`.** Its Step 0a confirms **where the instance folder lives** — *not* necessarily the directory you launched from (default suggestion: `~/Documents/chief-of-staff`, else `~/chief-of-staff`). A preflight (Step 0b) probes git, scheduling, hooks, and script execution, and records the verified results in `config.md`.
3. **Connectors:**
   - **Built-in Google connectors (Gmail / Calendar / Drive) are stub-only in CLI sessions** — they expose auth stubs, not the real tools. Connect them **once from Cowork or the Desktop app** (Customize → Connectors); CLI onboarding falls back to degraded mode (interview + file-drop) for email/calendar until then.
   - Recording connectors (Granola / Fathom / Fireflies) and Slack work fine in CLI — `/mcp` to approve OAuth.
4. This is the **fully verified runtime**: hooks fire (the outbound gate is structural), and session crons are durable as long as your machine runs them.

> **`setup.sh` is NOT used on this path either** — the plugin install already makes the skills invocable everywhere.

---

## Path 3 — Clone (dev / no plugin)

For hacking on the engine, or if you'd rather not install a plugin.

```bash
git clone https://github.com/fontesgerards/chief-of-staff
cd chief-of-staff
./setup.sh            # symlinks engine/skills into .claude/ and .agents/
```

Then open the folder in your runtime and run onboarding first:

| Runtime | Invoke |
|---|---|
| **Claude Code** (CLI or the Code tab) | `/cos-onboarding` — then `/cos-meeting-prep`, `/cos-loop-closing`, … |
| **Codex** (CLI) | `$cos-onboarding` — or open the `/skills` menu and pick it (Codex uses `$skill-name`, not `/skill-name`) |

**What `setup.sh` wires — `.claude/` and `.agents/` only:**

- `.claude/skills → engine/skills` (Claude discovers `/<name>`)
- `.agents/skills → engine/skills` (Codex discovers `$<name>` / `/skills`)
- It does **not** create `.cursor/` — Cursor is not wired by the clone path (see the support table below).
- Always-loaded behavior comes from `CLAUDE.md` (Claude) and `AGENTS.md` (Codex) at the repo root, which point at `engine/INSTRUCTIONS.md`.

**Symlink notes (this path only):**

- `.claude/skills` and `.agents/skills` are committed as symlinks, so on macOS / Linux / WSL a fresh clone already works — `setup.sh` is only needed if you moved the folder or your runtime doesn't follow symlinked skill dirs.
- If skills don't show up: `./setup.sh --copy` copies instead of symlinking (use on native Windows or any runtime that won't traverse a symlinked `skills/` directory), then restart the runtime. Trade-off: copies drift from `engine/skills/` — re-run after editing a skill.

---

## What each runtime supports

| Runtime | Support level | Works | Doesn't |
|---|---|---|---|
| **Claude Code** (CLI / Code tab) | **Full** — verified | Hooks + structural outbound gate; session crons (durable while your machine runs); all skills | Built-in Google connectors are stub-only in CLI sessions — connect once from Cowork/Desktop |
| **Claude Cowork** | Supported — degraded gate | Skills as slash commands; scheduled tasks (**~7-day expiry, app-open only**); plugin-tab + built-in connectors | Hooks don't fire ([#63360](https://github.com/anthropics/claude-code/issues/63360)) → read-only OAuth floor; preflight records the reality |
| **Codex** | Supported | Skills via `$cos-*` | No hooks; scheduling via external cron reading `config.md`'s `schedules:` block |
| **Cursor** | **Experimental** | A marketplace manifest exists (`engine/.cursor-plugin/plugin.json`) | Clone path unwired — `setup.sh` doesn't create `.cursor/`; untested end-to-end |

## Scheduled skills

`cos-consolidate-memory`, `cos-meeting-prep`, etc. run on the cadences in `instance/config.md` (`schedules:`). That block is the runtime-agnostic source of truth: native scheduling where the preflight verified it, an external `cron`/`launchd` job reading the same block where it didn't — see `engine/docs/U0-capability-spike.md` (a). On Cowork, remember the ~7-day expiry: interactive sessions check schedule liveness and prompt you to re-arm.
