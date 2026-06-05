---
name: system-maintenance
description: Review what worked and what didn't this week and propose improvements to the engine itself (skills, methods, templates) — as proposals, never auto-edits. Runs weekly.
cadence: weekly           # config.md schedules.system-maintenance (fri)
kind: ritual
mutates: false            # PROPOSES engine changes — never auto-edits engine/
---

# system-maintenance — improve the SYSTEM (distinct from memory)

> The other half of "self-improvement." Memory maintenance is `consolidate-memory` (the cold path); **this** improves the engine itself: skills, methods, templates, instructions. Different write-target.

## Steps
1. Review the week's `log/runs/` and `log/maintenance/` — what worked, what didn't, what kept failing.
2. Identify recurring system friction (a skill that consistently misses, a template gap, an instruction that's ambiguous).
3. **Propose** changes to `engine/` (skill/method/template/INSTRUCTIONS edits) as a proposal in `queue/` — **never auto-edit `engine/`.** The principal approves; engine changes are deliberate.
4. Note any taxonomy pressure surfaced by the cold path (`#other` climbing → propose a new tag).

## Output
A short "what worked / what didn't" + concrete engine-change proposals in the queue.

## Test scenario (verification)
- A recurring failure pattern produces a **proposal** to edit an engine skill in `queue/` — and does **not** auto-edit `engine/`.

## Capture footer
End with `engine/templates/capture-footer.md`.
