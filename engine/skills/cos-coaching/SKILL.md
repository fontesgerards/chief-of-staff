---
name: cos-coaching
description: Strengths-based weekly coaching grounded in your real meetings — one or two specific, role-relevant moves and an experiment for the week ahead.
cadence: weekly           # config.md schedules.coaching (fri)
kind: ritual
mutates: true             # hot-path: APPENDS the weekly note to episodic/coaching/ (Tier 0)
---

# coaching — strengths-based weekly development

> Uses `engine/methods/strengths-coaching.md`. Load `procedural/coaching.md` for the principal's preferred depth (default: lightweight nudges; set to structured review there if wanted).

## Steps
1. **Close last week's loop first.** Read the **most recent** `episodic/coaching/*.md`. Did its experiment actually show up in this week's episodes? Open the new note with that follow-up — *"last week you tried X; in the Plata call you…"* — honestly (it happened, partly, or not). On the **first-ever run** there's nothing to follow up — say so and proceed.
2. Read `core/identity.md` + `core/current-priorities.md` (role context).
3. Review the **past 7 days** of `episodic/` (meetings, decisions, interactions) for real moments.
4. Apply the strengths-coaching method: anchor on a strength, name one or two specific, role-relevant moves grounded in actual episodes. **Light week** (little to draw on) → don't manufacture feedback; give just the forward experiment.
5. End with a concrete experiment for the coming week.
6. **Write the note** from `engine/templates/coaching-note.md` to `episodic/coaching/YYYY-MM-DD.md` (append-only, Tier 0 — this is what next week's Step 1 reads; keep the **Experiment** section a single checkable behavior) and **deliver** it per `config.md` `delivery.coaching` (default: `.md` file under `state/briefs/`). Inward — no outward action.

## Output
A short, specific coaching note (not a list): the follow-up on last week's experiment, one or two strength-anchored moves, and this week's experiment. Stored in `episodic/coaching/` and delivered to the configured channel.

## Test scenarios (verification)
- A coaching run references real episodes and the principal's role/priorities from `core/`, and applies the strengths-based method.
- **Continuity:** the note opens by following up on the prior week's experiment (read from `episodic/coaching/`); the first-ever run notes there's nothing to follow up rather than inventing one.
- The note is written to `episodic/coaching/YYYY-MM-DD.md` and delivered to `delivery.coaching`; a light week yields just the forward experiment, not manufactured feedback.

## Output contract
| Artifact | Template | Path | Required frontmatter |
|---|---|---|---|
| coaching note | `engine/templates/coaching-note.md` | `memory/episodic/coaching/YYYY-MM-DD.md` | `type`, `date`, `covers`, `origin` |
| capture footer | `engine/templates/capture-footer.md` | `log/runs/<date>-<run>.md` | (appended block) |

Migration window (`schema:` absent or < 1 in `config.md`): read both old and new frontmatter/fact-line formats, write only the new; this note retires when migration completes.

## Capture footer
End with `engine/templates/capture-footer.md`.
