---
type: daily-brief
date: YYYY-MM-DD          # the run date (the evening before)
covers: YYYY-MM-DD        # the day this brief is FOR — the FILENAME uses THIS date: state/briefs/daily-brief-<covers>.md (skipped when Fri/Sat principal-local)
origin: derived           # observed | confirmed | inferred | imported | derived — assembled from memory + state; not a standing fact
---

# Your day — {{covers, weekday}}

## Top priorities
> The 3–5 things that matter most right now, from `core/current-priorities.md` — restated, not pasted. If priorities haven't been set yet: "No priorities on file — run `/cos-goal-setting` (or `/cos-onboarding` if the brain isn't seeded)."

- {{priority — and the one thing today that advances it, if any}}

## The day at a glance
> Non-declined events in the covered window, in order. Per-meeting prep briefs follow separately. If none: "No meetings — a maker day." If the calendar connector is unwired: "Calendar unwired — connect it (`config.md connectors:`) or drop events into `sources/calendar/`."

- {{start–end}} — {{event title}} ({{the one-line why-it-matters or prep pointer}})

## Approaching deadlines
> Commitments from `state/commitments.md` with `Due` within 3 days, plus anything overdue. If clear: "Nothing due in the next 3 days."

- {{who/what — due date, source}}

## On your desk
> The review queue at a glance, from `queue/`: pending proposals, open questions, staged memory diffs awaiting a decision. Counts, then a pointer. If empty: "Queue clear."

- {{N proposals · M questions · K memory diffs}} — run `/cos-review` to triage.
