---
name: cos-system-maintenance
description: Review what worked and what didn't this week and propose improvements to the engine itself (skills, methods, templates) — as proposals, never auto-edits. Runs weekly.
cadence: weekly           # config.md schedules.system-maintenance (fri)
kind: ritual
mutates: false            # PROPOSES engine changes — never auto-edits engine/
---

# system-maintenance — improve the SYSTEM (distinct from memory)

> The other half of "self-improvement." Memory maintenance is `cos-consolidate-memory` (the cold path); **this** improves the engine itself: skills, methods, templates, instructions. Different write-target. Load `procedural/system-maintenance.md` if present (e.g. how aggressive to be with proposals).

## Steps
1. **Read the friction signal — not just run logs.** Over the **past 7 days / since the last run**, mine the richest signals: `state/corrections.md` (tagged, and routed **by `skill`** for `#process`/`#omission` — so "which skill keeps missing" is *computable*, not eyeballed), the **cold path's health report** in `log/maintenance/` (per-tag correction rate, promotion-survival, mistagging, `#other` rate), plus `log/runs/` for hard failures.
2. **Run the deterministic validation sweep** (a script, never judgment). First check this session's host row under `config.md` → `runtime:`: if `script_exec` is `unavailable`, skip the command and report **"validation unavailable on this runtime"** in the note's Validation section — **never substitute an LLM approximation of the sweep**. Otherwise run verbatim (engine path per your install; date = today):
   ```
   python3 engine/validate_instance.py --instance <instance-root> --manifest <instance-root>/state/validation/findings-<YYYY-MM-DD>.md
   ```
   Report the stdout summary (error/warn counts, top items) in the maintenance note's Validation section. The sweep and this skill **NEVER edit memory** — findings are written to the manifest and fixed by the next cold-path run (`cos-consolidate-memory`), not here. Open findings carry a stable fingerprint + `first_seen:` (deduped against the previous manifest), so a still-open item isn't re-reported as new.
3. **Identify recurring friction** — a skill that consistently misses, a template gap, an ambiguous instruction, repeated `#other` (a taxonomy defect).
4. **Apply the engine-vs-procedural boundary test** — *this is the whole discipline.* For each friction pattern, ask **"is this structural or principal-specific?"**
   - **Principal-specific** (a *this-principal* preference: tone, emphasis, a checklist item that suits them) → **not yours.** Leave it to the **cold path**, which promotes `#process`/`#omission` into `procedural/<skill>.md`. Do **not** propose an engine edit.
   - **Structural** (would mislead *any* principal: a step that's wrong for everyone, an ambiguous instruction, a template gap, a taxonomy defect) → **propose an `engine/` change.** A pattern only generalizes after it shows up across distinct contexts — don't promote a one-off to the engine.
5. **Propose** structural changes to `engine/` (skill/method/template/INSTRUCTIONS edits) as a proposal in `queue/` — **never auto-edit `engine/`.** The principal approves; engine changes are deliberate.
6. **Deliver** the summary (from `engine/templates/system-maintenance-note.md`) per `config.md` `delivery.system-maintenance` (default: `.md` file under `state/briefs/`); engine proposals stay in `queue/`. The note records the **engine-vs-procedural boundary call** (its "Left to the cold path" section). **Clean week** (no structural friction) → the *"No changes proposed"* form, not a manufactured proposal.

## Output
A "what worked / what didn't" summary on the configured channel + any **structural** engine-change proposals in the queue. Principal-specific friction is left to the cold path; a healthy week yields a short no-op note.

## Test scenarios (verification)
- A recurring **structural** failure pattern produces a **proposal** to edit an engine skill in `queue/` — and does **not** auto-edit `engine/`.
- A **principal-specific** correction (a preference) is **not** turned into an engine proposal — it's left for the cold path to promote into `procedural/`.
- The friction review draws on `corrections.md` + the cold-path health report, not run logs alone; a clean week yields a short "no changes proposed" note delivered to `delivery.system-maintenance`.
- The validation sweep ran via the verbatim `validate_instance.py` command (or reported "validation unavailable on this runtime" where `script_exec` is `unavailable`); its summary appears in the note, the manifest landed under `state/validation/`, and **no memory file was edited** by this run.

## Output contract
| Artifact | Template | Path | Required frontmatter |
|---|---|---|---|
| maintenance note | `engine/templates/system-maintenance-note.md` | `state/briefs/system-maintenance-YYYY-MM-DD.md` | `type`, `date`, `covers`, `origin` |
| validation findings manifest | — (written by `engine/validate_instance.py`, not the LLM) | `state/validation/findings-YYYY-MM-DD.md` | `type`, `date`, `schema_seen` |
| capture footer | `engine/templates/capture-footer.md` | `log/runs/<date>-<run>.md` | (appended block) |

Engine-change proposals append to the review surface `queue/review/review-<date>.md` (raw text, no frontmatter schema).

## Capture footer
End with `engine/templates/capture-footer.md`.
