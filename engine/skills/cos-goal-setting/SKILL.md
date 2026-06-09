---
name: cos-goal-setting
description: Monthly goals and prioritization — reviews progress, then proposes an updated set of current priorities for your approval.
cadence: monthly          # config.md schedules.goal-setting (1st)
kind: ritual
mutates: true             # hot-path: APPENDS the monthly snapshot to episodic/goals/ (Tier 0). The core/ priorities edit is PROPOSED (Tier 2), not a direct mutate.
---

# goal-setting — monthly goals & prioritization

> Generic process. Per-principal adaptations live in `instance/memory/procedural/goal-setting.md` — **load it first** and apply its rules (cadence emphasis, what "a goal" means here, how aggressive to prune).

## Steps
1. **Read last month's snapshot first.** Load the **most recent** `episodic/goals/*.md` — the goals/priorities actually set last cycle (an immovable record; `core/current-priorities.md` has since moved). Plus `core/current-priorities.md` (live set), recent `episodic/milestones/` & `decisions/`, and `state/`. On the **first-ever run** there's no snapshot — say so and baseline from `current-priorities.md`.
2. **Review progress against last month's snapshot** — what advanced, what stalled, what slipped (grounded in milestones/decisions, not impressions).
3. Use `methods/problem-solving.md` if the principal is weighing a real trade-off.
4. **Propose** an updated `core/current-priorities.md`. Editing `core/` is **Tier 2** — surface the change as a raw-diff proposal in the review surface for approval. (Propose-only; never auto-edit `core/`.)
5. **Write the snapshot** from `engine/templates/goals-snapshot.md` to `episodic/goals/YYYY-MM.md` (append-only, Tier 0): the month-in-review + the goals/priorities **as committed** this cycle — this is what next month's Step 1 reads. Record the priorities *as they stand approved*, not the unapproved Tier-2 draft. **Deliver** the month-in-review per `config.md` `delivery.goal-setting` (default: `.md` file under `state/briefs/`).

## Output
A proposed priority update (Tier-2 approval, to the queue) + a month-in-review delivered to the configured channel + the `episodic/goals/` snapshot for continuity.

## Test scenarios (verification)
- A goals run that lowers a stated priority routes to a **Tier-2 approval** (editing `core/current-priorities.md`), not an auto-edit.
- **Continuity:** the run reviews progress against last month's `episodic/goals/` snapshot; the first-ever run baselines from `current-priorities.md` rather than inventing a prior month.
- A snapshot is written to `episodic/goals/YYYY-MM.md` recording the committed (not draft) priorities; the month-in-review is delivered to `delivery.goal-setting`.

## Capture footer
End with `engine/templates/capture-footer.md`.
