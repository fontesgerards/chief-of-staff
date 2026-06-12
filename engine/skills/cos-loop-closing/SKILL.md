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
   - **Going quiet** — a key relationship with no real contact inside `config.md` `loop_closing.relationship_stale_after_days` (default 28). Scope: `semantic/people/` records with `key: true` only, never `status: former` or opted-out people. **Contact = the max of three signals** — the most recent `episodic/meetings/` note naming them; a `status: sent` outbound proposal addressed to them — scan `queue/outbound/` **and** the retired-proposal destination under `log/`, **bounded by filename date-prefix ≥ today − `relationship_stale_after_days`** (older files can't clear the flag, so never open them); queue retention is shorter than this threshold, so retirement must move-to-log, never delete (`config.md` `queue.retain_resolved_days`); and the person record's `last_contacted:` stamp (written by `cos-inbox-sweep`). A `last_touched` bump is **not** contact — a brief merely mentioning someone clears nothing.
3. **Propose a next step / owner** for each flagged item. Where it needs an outward nudge, write a **proposal** to `queue/outbound/` — in the principal's voice (`core/voice.md` + `procedural/drafting.md`); never send. **Fill the dashboard display fields** (`engine/templates/proposal.md`) so it renders as a rich card: `topic:` = the account/project the loop belongs to (else the bucket — Unassigned / Stalled / Overdue / Going quiet); `source:` = `loop` (`relationship` for going-quiet outreach); `context:` = one line naming the loop; `## What happened` = the loop's current state (owner-less, no movement since `Last update`, or past `Due`); `## Why this is in the sweep` = the staleness/ownership trigger that flagged it. **`reversibility:` is derived from the tool, never assumed:** `reversible` only when the tool merely creates a draft in the principal's own account (e.g. Gmail `create_draft` — inward per the gate); `irreversible` for any tool that itself transmits — irreversible always needs explicit approval regardless of the dial. **Going-quiet outreach is gated by the no-duplicate rule:** re-flag the person in the brief every week they stay quiet, but never draft a second nudge while **any** `pending`/`feedback` proposal to that person exists in the queue (a live thread or an earlier nudge supersedes a "long time no talk").
4. **Deliver** the summary (from `engine/templates/loop-closing-brief.md`) per `config.md` `delivery.loop-closing` (default: `.md` file under `state/briefs/`), grouped **unassigned / stalled / overdue / going quiet**. Delivery to the principal's own channel is inward, not a proposal.
   - **When a loop is blocked on a decision only the principal can make** — who should own it, whether to drop it, which of two paths to take — don't guess and don't bury it in prose. Emit it as an **open question** so it becomes an answerable card in the review dashboard's **To review** tab: `python engine/skills/cos-review/review_lib.py add-question <instance_dir>/state/pending-questions.md "<the question>" --why "<why it matters>" --ts <iso>`. Surface uncertainty *by exception*, not for every loop.
5. **If nothing is flagged, skip the run** — no summary, no empty file (as with meeting-follow-up; meeting-prep's *per-meeting* briefs likewise skip on empty, though its daily brief still renders).

> **Why this skill does not stamp `Last update`:** stamping on mere surfacing would make every loop look "moved" each week and mask real staleness. loop-closing only reads movement; it keeps surfacing a loop until something real (a meeting via `cos-meeting-follow-up`, or the principal) advances it. Re-surfacing a loop that already has a queued nudge is intended — nothing drops silently.

## Output
A loop-closing summary (unassigned / stalled / overdue / going quiet, with suggested owners/next steps) on the configured channel; outward nudges queued in the principal's voice. On a clean slate, no output.

## Test scenarios (verification)
- An unowned loop, an open loop whose `Last update` exceeds `stalled_after_days`, and an overdue commitment are each surfaced with a suggested owner/next step.
- A loop that moved within the window (recent `Last update`) is **not** flagged stalled — movement, not age (Opened).
- A commitment with no `Who` is flagged unassigned; a past-`Due` commitment is flagged overdue.
- A `key: true` person whose last episodic meeting, sent outbound, and `last_contacted:` are **all** older than `relationship_stale_after_days` is flagged going quiet; a non-key person never is.
- A mention-only `last_touched` bump does **not** clear a going-quiet flag (the signal is contact, not mention).
- A key person whose only contact is a sent proposal already retired to `log/` is **not** flagged (the sent-signal scan covers the post-retention destination).
- A key person with a recent `last_contacted:` stamp (the principal answered their email) is **not** flagged.
- A flagged person with a `pending`/`feedback` proposal already in the queue is re-flagged in the brief but gets **no second draft**; `status: former` people are never flagged.
- Any nudge is a queued proposal **in the principal's voice**, never a send.
- A clean slate (nothing flagged, nothing going quiet) produces **no output**; loop-closing leaves `Last update` untouched.

## Output contract
| Artifact | Template | Path | Required frontmatter |
|---|---|---|---|
| loop-closing brief | `engine/templates/loop-closing-brief.md` | `state/briefs/loop-closing-YYYY-MM-DD.md` | `type`, `date`, `origin` |
| outward nudge | `engine/templates/proposal.md` | `queue/outbound/YYYY-MM-DD-<slug>.md` | `type`, `date`, `skill`, `status`, `reversibility`, `tool`, `args_digest` |
| capture footer | `engine/templates/capture-footer.md` | `log/runs/<date>-<run>.md` | (appended block) |

Migration window (`schema:` absent or < 1 in `config.md`): read both old and new frontmatter/fact-line formats, write only the new; this note retires when migration completes.

## Capture footer
End with `engine/templates/capture-footer.md`.
