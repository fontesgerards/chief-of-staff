---
name: cos-meeting-prep
description: Prepare you for upcoming meetings — pull context on attendees and accounts, surface open loops and commitments, and suggest an agenda. Runs daily; invoke anytime before a call.
cadence: daily            # config.md schedules.meeting-prep
kind: ritual
mutates: false            # reads memory + delivers a brief to state/briefs/; writes no memory
---

# meeting-prep — prepare the principal for what's ahead

> Generic process. Per-principal adaptations live in `instance/memory/procedural/meeting-prep.md` — **load it first** and apply its rules/checklist.

## Steps
1. **Read state first** (`INSTRUCTIONS.md` §3): `state/current.md`, `open-loops.md`, `commitments.md`. Load `procedural/meeting-prep.md` and apply its rules/checklist.
2. **Pull the next 24 hours of meetings** from calendar (connector or `sources/calendar/`). Include all **non-declined** events (accepted / tentative / no-response); skip ones the principal has declined. **If there are none, skip the run** — produce no brief and no empty file (don't emit a "nothing to prep" note unless `procedural/` says otherwise).
3. **For each meeting, build a brief** from `engine/templates/meeting-prep-brief.md`:
   - **Attendees & accounts** — load via the `semantic/` router: only the relevant `people`/`accounts`, plus close neighbors via `relationships`. Check `relationships/` for any **sensitivity** (`#relationship` learnings).
   - **Open loops & commitments** tied to these attendees/accounts, from `state/`.
   - **Recent context** — relevant `episodic/` (last meeting, recent decisions) and any fresh `sources/`.
   - **Objective & agenda** — top-down (`minto.md`): the goal, the 2–3 things to cover, the asks, the risks. Apply procedural rules (e.g. "lead with their pain, not our product" if learned).
4. **Deliver** per `config.md` `delivery.meeting-prep` (default: a Markdown file in the instance folder, `state/briefs/meeting-prep-<date>.md`; other wired channels offered at onboarding). Delivering to the principal's **own** file/inbox/DM is a notification (**inward**) — not an outward proposal. Purely preparatory; no message is sent on anyone else's behalf.

## Output
A prep brief per meeting (title, who's attending, objective, context, key reminders), delivered to the configured channel. On an empty 24h window, no output.

## Test scenarios (verification)
- A calendar with meetings in the next 24h yields one brief per non-declined event, each built from the template; loads only relevant `semantic/people` + `episodic` via routers (not the whole archive); surfaces open loops.
- A **declined** event is excluded; an empty 24h window produces **no brief and no file**.
- A known high-sensitivity relationship surfaces its caution in the brief.
- The brief lands on the configured `delivery.meeting-prep` channel (default `.md` file under `state/briefs/`).
- After the principal edits the agenda, a correction record is appended for the cold path.

## Output contract
| Artifact | Template | Path | Required frontmatter |
|---|---|---|---|
| prep brief (one per meeting) | `engine/templates/meeting-prep-brief.md` | `state/briefs/meeting-prep-YYYY-MM-DD.md` | `type`, `date`, `meeting`, `when`, `entities`, `origin` |
| capture footer | `engine/templates/capture-footer.md` | `log/runs/<date>-<run>.md` | (appended block) |

Migration window (`schema:` absent or < 1 in `config.md`): read both old and new frontmatter/fact-line formats, write only the new; this note retires when migration completes.

## Capture footer
End with `engine/templates/capture-footer.md`.
