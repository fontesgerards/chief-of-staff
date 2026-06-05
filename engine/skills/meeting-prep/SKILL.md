---
name: meeting-prep
description: Prepare you for upcoming meetings — pull context on attendees and accounts, surface open loops and commitments, and suggest an agenda. Runs daily; invoke anytime before a call.
cadence: daily            # config.md schedules.meeting-prep
kind: ritual
---

# meeting-prep — prepare the principal for what's ahead

> Generic process. Per-principal adaptations live in `instance/memory/procedural/meeting-prep.md` — **load it first** and apply its rules/checklist.

## Steps
1. **Read state first** (`INSTRUCTIONS.md` §3): `state/current.md`, `open-loops.md`, `commitments.md`.
2. **Pull the meeting(s).** From calendar (connector or `sources/calendar/`). For each upcoming meeting:
3. **Load attendees & accounts** via the `semantic/` router — only the relevant `people`/`accounts`, plus close neighbors via `relationships`. Check `relationships/` for any **sensitivity** (`#relationship` learnings).
4. **Surface open loops & commitments** tied to these attendees/accounts from `state/`.
5. **Recent context** — relevant `episodic/` (last meeting, recent decisions) and any fresh `sources/`.
6. **Propose an agenda** — top-down (`minto.md`): the goal, the 2–3 things to cover, the asks, the risks. Apply procedural rules (e.g. "lead with their pain, not our product" if learned).

## Output
A concise prep brief per meeting (who, why it matters, open loops, suggested agenda, watch-outs). No outward action — purely preparatory.

## Test scenarios (verification)
- Given an event with known attendees, loads only relevant `semantic/people` + `episodic` via routers (not the whole archive); surfaces open loops; proposes an agenda.
- A known high-sensitivity relationship surfaces its caution in the brief.
- After the principal edits the agenda, a correction record is appended for the cold path.

## Capture footer
End with `engine/templates/capture-footer.md`.
