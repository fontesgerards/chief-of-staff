---
name: cos-onboarding
description: Set up your AI Chief of Staff — interviews you, observes your email/calendar to draft a profile, captures your writing voice, and seeds your private memory. Run this first. Re-run to re-seed.
disable-model-invocation: true
kind: installer
run: once (or to re-seed)
---

# onboarding — the installer (observe, don't make me teach you)

> One conversation that stands up a working `instance/` from the engine's `templates/`. For the future product, steps 1–8 **are** the activation funnel — each new person just talks to it. Scoped thin: wire only **email / calendar / recordings** (Slack/SendBlue deferred).
>
> **Where the instance goes:** `instance/` is created in the **current working directory** — the folder the principal launched the runtime from. The engine (templates, methods, this skill) may be a globally-installed plugin elsewhere; resolve engine files from the plugin package and `instance/` from the working directory (see engine `AGENTS.md` → "Two roots"). If an `instance/` already exists here, confirm before re-seeding.
>
> **Prerequisite:** run the U0 capability spike first (engine `docs/U0-capability-spike.md`). It tells you whether connectors are live (step 5) and whether the extractor is structurally isolated.

## The seven steps

1. **Ask what they do & their goals.** Role, company, mandate, who they serve, what "good" looks like. → drafts `core/identity.md`.
2. **Observe how they work.** Via the **read-only extractor**, ingest recent email/calendar/docs to *draft* a profile — operating context, key people/accounts, recurring patterns. → drafts `core/operating-context.md`, seeds `semantic/` entities.
3. **Confirm by exception.** Show what was inferred; ask **only** where confidence is low. Don't ask what you can observe.
4. **Gather voice from real samples.** Pull representative sent messages; derive tone/length/avoid constraints → `core/voice.md` (respect its budget). Learned habits later accrue in `procedural/drafting.md`.
5. **Connect tools.** Wire **email / calendar / recordings** only. **Credentials are delegated to the runtime's connector auth — never written to `config.md` or any file** (config references connectors by name). Defer Slack/SendBlue without blocking.
6. **Seed the five-type memory** from `engine/templates/`: `core/`, `semantic/`, `episodic/` (recent), `procedural/` (empty or template), `sources/` (with retention), plus `state/`, `queue/`, `log/`, optional `index/`. **All seeded facts carry `origin: imported`** — they won't auto-trust into `core`/`procedural` (tier gate). A **dense, correct seed** both bootstraps usefulness and hardens the brain against later poisoning.
7. **Write `config.md` & schedule.** Autonomy default = propose-only; fill `connectors:` (names), `schedules:` (cadence per skill), `queue:` lifecycle, `write_back:` tuning. Then initialize the `instance/` backup repo (`.backup-instructions.md`).
8. **Write the working-folder entry files.** So behavior auto-loads every session (especially when the engine is a globally-installed plugin), write a `CLAUDE.md` and `AGENTS.md` into the working directory (next to `instance/`). Keep them thin: identity one-liner + the **safety floor inlined** (never send outward without approval; never edit `core/` outside a Tier-2 proposal) + "the full behavior contract lives in the chief-of-staff engine's `INSTRUCTIONS.md` — read it first." Inlining the safety floor means the folder is safe even if the plugin path can't be resolved. Use `engine/templates/entry-CLAUDE.md` as the template.

## Output
A populated, scheduled, working `instance/` in the current folder, plus `CLAUDE.md`/`AGENTS.md` entry files: opening this folder in the runtime + this run = a functioning system.

## Test scenarios (verification)
- **Cold start:** running against a sample mailbox/calendar produces a populated `instance/` (core seeded, some `semantic/` entities, `config.md` written, schedules set).
- **Confirm-by-exception:** inferred facts shown; only low-confidence items asked.
- **Origin tagging:** every seeded fact is `origin: imported` (grep) — proves the tier gate won't auto-trust them.
- **Connector scope:** wires email/calendar/recordings, explicitly skips Slack/SendBlue without blocking; no credential literal is written to `config.md`.
- **Voice seed:** `core/voice.md` populated from real samples, within budget.

> **Deferred to product track:** multi-tenant regeneration + data-isolation (running against a second identity with no bleed, instance-root path scoping). Not a v1-of-one concern; the engine/instance split keeps the seam clean until a real second tenant exists.

## Capture footer
End with `engine/templates/capture-footer.md`.
