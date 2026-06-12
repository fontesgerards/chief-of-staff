---
name: cos-meeting-prep
description: Start your day prepared — a chief-of-staff daily brief (priorities, calendar, deadlines, review queue) plus per-meeting prep with attendee context, open loops, and a suggested agenda. Runs daily; invoke anytime before a call.
cadence: daily            # config.md schedules.meeting-prep
kind: ritual
mutates: false            # reads memory + delivers briefs to state/briefs/; writes no memory
---

# meeting-prep — prepare the principal for what's ahead

> Generic process. Per-principal adaptations live in `instance/memory/procedural/meeting-prep.md` — **load it first** and apply its rules/checklist.

## Steps
1. **Read state first** (`INSTRUCTIONS.md` §3): `state/current.md`, `open-loops.md`, `commitments.md`. Load `procedural/meeting-prep.md` and apply its rules/checklist.
2. **Render the daily brief** from `engine/templates/daily-brief.md` → `state/briefs/daily-brief-<covered-day>.md`. The **covered day** is the day the next-24h window lands on (this run fires the evening before). **Skip the daily brief when the covered day is a Friday or Saturday** (principal-local — `config.md` `timezone:`); per-meeting briefs below are unaffected by the skip. The brief renders **even when the window has no meetings** — priorities, deadlines, and the queue still matter on a maker day. Sections, each degrading gracefully:
   - **Top priorities** — restated from `core/current-priorities.md`; if absent (pre-onboarding), say so and point at `/cos-goal-setting` — never invent priorities.
   - **The day at a glance** — the window's non-declined events in order, one line each; "No meetings — a maker day." when empty; if the calendar connector is unwired (`connectors.calendar` ≠ connected/verified and no `sources/calendar/` drops), an explicit "calendar unwired" line — not a skipped run.
   - **Approaching deadlines** — `state/commitments.md` rows with `Due` within 3 days, plus anything overdue.
   - **On your desk** — counts of pending proposals (`queue/outbound/`), open questions (`state/pending-questions.md`), and staged memory diffs (`queue/review/memory/`), with a `/cos-review` pointer.
3. **Pull the next 24 hours of meetings** from calendar (connector or `sources/calendar/`). Include all **non-declined** events (accepted / tentative / no-response); skip ones the principal has declined. **If there are none, skip the per-meeting briefs** — produce no empty prep files (the daily brief from step 2 still stands; don't emit a "nothing to prep" note unless `procedural/` says otherwise).
4. **For each meeting, build a brief** from `engine/templates/meeting-prep-brief.md`:
   - **Attendees & accounts** — load via the `semantic/` router: only the relevant `people`/`accounts`, plus close neighbors via `relationships`. Check `relationships/` for any **sensitivity** (`#relationship` learnings).
   - **Open loops & commitments** tied to these attendees/accounts, from `state/`.
   - **Recent context** — relevant `episodic/` (last meeting, recent decisions) and any fresh `sources/`.
   - **Objective & agenda** — top-down (`minto.md`): the goal, the 2–3 things to cover, the asks, the risks. Apply procedural rules (e.g. "lead with their pain, not our product" if learned).
5. **Deliver** per `config.md` `delivery.meeting-prep` (default: Markdown files in the instance folder under `state/briefs/`; other wired channels offered at onboarding). Delivering to the principal's **own** file/inbox/DM is a notification (**inward**) — not an outward proposal. Purely preparatory; no message is sent on anyone else's behalf.

## Output
A daily brief (priorities, day at a glance, deadlines, review queue — skipped on Fri/Sat covered days) plus a prep brief per meeting (title, who's attending, objective, context, key reminders), delivered to the configured channel. A meeting-free weekday still gets the daily brief; an empty window adds no per-meeting files.

## Test scenarios (verification)
- A meeting-free Tuesday still yields a daily brief (priorities + "No meetings" + deadlines + queue counts) and **no** per-meeting briefs.
- A Thursday-evening run (covering Friday) yields **no daily brief**, but a Friday meeting still gets its per-meeting prep brief; same for Saturday coverage.
- Pre-onboarding (no `core/current-priorities.md`) renders the brief with the "no priorities on file" line — not a crash or a skipped run.
- A calendar connector with `status: pending` and no `sources/calendar/` drops degrades to the "calendar unwired" line in the daily brief.
- A calendar with meetings in the next 24h yields one brief per non-declined event, each built from the template; loads only relevant `semantic/people` + `episodic` via routers (not the whole archive); surfaces open loops.
- A **declined** event is excluded from both the daily brief's day-at-a-glance and the per-meeting briefs.
- A known high-sensitivity relationship surfaces its caution in the brief.
- The briefs land on the configured `delivery.meeting-prep` channel (default `.md` files under `state/briefs/`).
- After the principal edits the agenda, a correction record is appended for the cold path.

## Output contract
| Artifact | Template | Path | Required frontmatter |
|---|---|---|---|
| daily brief | `engine/templates/daily-brief.md` | `state/briefs/daily-brief-YYYY-MM-DD.md` | `type`, `date`, `covers`, `origin` |
| prep brief (one per meeting) | `engine/templates/meeting-prep-brief.md` | `state/briefs/meeting-prep-YYYY-MM-DD.md` | `type`, `date`, `meeting`, `when`, `entities`, `origin` |
| capture footer | `engine/templates/capture-footer.md` | `log/runs/<date>-<run>.md` | (appended block) |

Migration window (`schema:` absent or < 1 in `config.md`): read both old and new frontmatter/fact-line formats, write only the new; this note retires when migration completes.

## Capture footer
End with `engine/templates/capture-footer.md`.
