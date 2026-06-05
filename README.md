# AI Chief of Staff

A personal Chief of Staff that runs on top of an agent runtime (Claude Cowork / Codex): scheduled and on-demand skills, backed by a plain-text Markdown memory store, that prepares you for what's ahead, closes loops, coaches you, and **gets sharper the longer it runs**. It installs and configures itself by interviewing you.

It does not act on the world by default. It **proposes**; you approve.

> Build artifact of [[AI Chief of Staff — Build Plan]]. Design: [[AI Chief of Staff]] · validation: [[AI Chief of Staff — Architecture Evaluation]] · loop spec: [[AI Chief of Staff — write-back method]].

## Install

**As a plugin (easiest)** — Claude Code:
```text
/plugin marketplace add fontesgerards/chief-of-staff
/plugin install chief-of-staff@chief-of-staff
```
Then, in the folder where you want your brain to live: `/cos-onboarding`. Codex uses the same `engine/` package — see `PUBLISH.md`. Publishing steps + the naming/collision note: `PUBLISH.md`.

**Or clone (dev / no plugin):** `git clone …`, `./setup.sh`, open the folder, `/cos-onboarding`. See `INSTALL.md`.

The **engine** is the shared plugin; your **instance** (private brain) is created by `/cos-onboarding` in your own folder — it never lives in the plugin.

## The two halves

```
chief-of-staff/
├─ CLAUDE.md / AGENTS.md  ← always-loaded entry (Claude / Codex) → engine/INSTRUCTIONS.md
├─ setup.sh / INSTALL.md  ← one command to make skills invocable (/cos-onboarding, $cos-onboarding)
├─ engine/      ← git, shareable, identical for everyone (THE PRODUCT — no personal data)
│  ├─ INSTRUCTIONS.md   global behavior + autonomy + memory-access conventions
│  ├─ skills/cos-<name>/SKILL.md   invocable skills — cos-onboarding, cos-meeting-prep, cos-consolidate-memory, …
│  ├─ methods/          write-back, problem-solving, minto, coaching, PEI
│  ├─ templates/        entity schemas, memory-file + capture + proposal templates
│  └─ docs/             capability spike + write-isolation config + build notes
├─ .claude/skills → engine/skills   (symlink — Claude discovers /<name>)
├─ .agents/skills → engine/skills   (symlink — Codex discovers $<name>)
└─ instance/   ← local + private, GITIGNORED here; its own separate backup repo (one person's brain)
   ├─ config.md         identity, goals, autonomy level, connectors, schedules
   ├─ memory/           core · semantic · episodic · procedural · sources · archive
   ├─ state/            current run, open loops, commitments, pending questions, corrections
   ├─ queue/            proposals awaiting approval (outbound · approvals · review)
   ├─ log/              run history + maintenance changelogs
   └─ index/            optional, generated, rebuildable from Markdown
```

**Why the split:** to productize later, ship `engine/` and let the onboarding skill regenerate a fresh `instance/` for each new person. Nothing personal ever lives in the shared repo.

## Status

v1 scaffold complete; skills are invocable as commands (run `./setup.sh`, then `/cos-onboarding` in Claude or `$cos-onboarding` in Codex — see `INSTALL.md`). **U0 capability spike resolved (2026-06-04):** scheduling ✓, connectors ✓, write-isolation ✓ (structural — enforced per-run via Claude Code `permissions.deny`+sandbox or Codex permissions profile; recipes in `engine/docs/write-isolation-config.md`). KTD-5 stays "structural." Next: run `/cos-onboarding` to seed a real `instance/`, and add a private remote to the instance backup repo.

## Core principles

1. **Engine vs. instance are separate** — the shareable framework never contains anyone's personal data.
2. **Plain text is the brain** — memory, methods, and skills are Markdown; the runtime is swappable.
3. **Propose, never act (by default)** — every outward action lands in a review queue. Autonomy is a dial, not a hardcode.
4. **Inward writes ≠ outward actions** — memory writes are made safe by append-only capture + git-reversible consolidation + confidence tiers, not by gating every write on approval.
5. **Observe first, ask by exception** — learn how you work from email/docs/calendar; only ask where genuinely uncertain.
6. **It must maintain itself** — memory and the system both decay; scheduled maintenance is first-class.
