---
name: cos-loop-closing
description: Surface what's unassigned, stalled, or ownerless across your open loops and commitments, and propose next steps. Runs weekly.
cadence: weekly           # config.md schedules.loop-closing (mon)
kind: ritual
mutates: false            # reads state + proposes; does NOT stamp Last update (see below)
---

# loop-closing — what's unassigned, stalled, or ownerless

> Generic process. Per-principal adaptations live in `instance/memory/procedural/loop-closing.md` — **load it first** and apply its rules (e.g. loops that never need an owner, custom staleness per category, who to nudge how).

## Steps
1. **Read** `state/open-loops.md` + `state/commitments.md`. Load `procedural/loop-closing.md`.
2. **Flag across both files:**
   - **Unassigned** — `open-loops.Owner` empty (or a commitment with no `Who`).
   - **Stalled** — an open loop whose `Last update` is older than `config.md` `loop_closing.stalled_after_days` (default 7). This measures **movement, not age** — `Last update` is stamped by skills that actually advance a loop, so a long-running loop that's still moving is *not* flagged.
   - **Overdue** — a commitment whose `Due` is in the past and not closed.
3. **Propose a next step / owner** for each flagged item. Where it needs an outward nudge, write a **proposal** to `queue/outbound/` — in the principal's voice (`core/voice.md` + `procedural/drafting.md`); never send.
4. **Deliver** the summary (from `engine/templates/loop-closing-brief.md`) per `config.md` `delivery.loop-closing` (default: `.md` file under `state/briefs/`), grouped **unassigned / stalled / overdue**. Delivery to the principal's own channel is inward, not a proposal.
5. **If nothing is flagged, skip the run** — no summary, no empty file (as with meeting-prep / follow-up).

> **Why this skill does not stamp `Last update`:** stamping on mere surfacing would make every loop look "moved" each week and mask real staleness. loop-closing only reads movement; it keeps surfacing a loop until something real (a meeting via `cos-meeting-follow-up`, or the principal) advances it. Re-surfacing a loop that already has a queued nudge is intended — nothing drops silently.

## Output
A loop-closing summary (unassigned / stalled / overdue, with suggested owners/next steps) on the configured channel; outward nudges queued in the principal's voice. On a clean slate, no output.

## Test scenarios (verification)
- An unowned loop, an open loop whose `Last update` exceeds `stalled_after_days`, and an overdue commitment are each surfaced with a suggested owner/next step.
- A loop that moved within the window (recent `Last update`) is **not** flagged stalled — movement, not age (Opened).
- A commitment with no `Who` is flagged unassigned; a past-`Due` commitment is flagged overdue.
- Any nudge is a queued proposal **in the principal's voice**, never a send.
- A clean slate (nothing flagged) produces **no output**; loop-closing leaves `Last update` untouched.

## Output contract
| Artifact | Template | Path | Required frontmatter |
|---|---|---|---|
| loop-closing brief | `engine/templates/loop-closing-brief.md` | `state/briefs/loop-closing-YYYY-MM-DD.md` | `type`, `date`, `origin` |
| outward nudge | `engine/templates/proposal.md` | `queue/outbound/YYYY-MM-DD-<slug>.md` | `type`, `date`, `skill`, `status`, `reversibility`, `tool`, `args_digest` |
| capture footer | `engine/templates/capture-footer.md` | `log/runs/<date>-<run>.md` | (appended block) |

## Capture footer
End with `engine/templates/capture-footer.md`.
