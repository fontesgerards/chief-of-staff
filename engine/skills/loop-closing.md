---
skill: loop-closing
cadence: weekly           # config.md schedules.loop-closing (mon)
kind: ritual
---

# loop-closing — what's unassigned, stalled, or ownerless

## Steps
1. Read `state/open-loops.md` + `state/commitments.md`.
2. Flag loops that are: **unassigned** (no owner), **stalled** (no movement since N days), or **overdue**.
3. For each, propose a next step / owner. Where it needs an outward nudge, write a **proposal** to `queue/outbound/` (never send).
4. Surface the summary in the daily brief.

## Output
A loop-closing summary with suggested owners/next steps; outward nudges queued.

## Test scenario (verification)
- Stalled/ownerless items in `state/open-loops.md` are surfaced with suggested owners/next steps; any nudge is a queued proposal, not a send.

## Capture footer
End with `engine/templates/capture-footer.md`.
