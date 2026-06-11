---
name: cos-meeting-follow-up
description: At end of day, capture outcomes from the day's meetings into memory, extract commitments, and draft any follow-up messages as proposals for your approval. Runs daily across the last 24h; invoke anytime after a call.
cadence: daily            # config.md schedules.meeting-follow-up (end of day); also invoke on-demand after a call
kind: ritual
mutates: true             # hot-path: APPENDS to episodic/ + state/ (never destructive — that's the cold path)
---

# meeting-follow-up — close the loop after the day's meetings

> Where the three write-targets meet in one run (a clean demonstration of inward-vs-outward, `INSTRUCTIONS.md` §2). The **inverse of `cos-meeting-prep`**: prep looks 24h *ahead*, follow-up sweeps 24h *behind*. Absorbs the old standalone "to-do extraction." Load `procedural/meeting-follow-up.md` first.

## Steps
1. **Select the meetings to process.** End-of-day run: every calendar meeting in the **past 24 hours** (the inverse of prep's look-ahead). On-demand: the call just finished. For each, locate its transcript/notes (recording connectors — Granola/Zoom/Fathom/Fireflies — or `sources/transcripts/`). **Skip a meeting when:** it's already captured (an `episodic/meetings/` note exists for it — the run is **idempotent**, safe to re-run), its transcript **isn't ready yet** (recording lag — leave it for the next run, don't write a half-empty note), or it was declined / a no-show. **If nothing is left, skip the run** (no empty output).
2. **Consume the staged extraction — don't extract inline.** Read the transcript's staged tuples/summary (`log/runs/` + `sources/transcripts/`) produced by the **isolated** `cos-extract-from-sources` pass. If the transcript isn't staged yet, **trigger a restricted extractor run** for it and wait — never open the raw transcript or extract in this skill's own (memory-capable) profile (that would forfeit the isolation guarantee — see the extractor's invocation contract).
3. **Resolve attendees & accounts.** Match the meeting to its calendar event and resolve speakers/attendees against `semantic/` (people/accounts) so the episodic note's `entities` backlinks connect. Unknown attendees → stage for `cos-entity-enrichment`; don't invent.
4. **Capture outcomes → episodic.** Write `memory/episodic/meetings/YYYY-MM-DD-<slug>.md` (derived, restated — not verbatim) with resolved `[[entity]]` backlinks.
5. **Extract commitments → state.** Append to `state/commitments.md` (who/what/due/source).
6. **Open/close loops → state.** Update `state/open-loops.md`; **stamp `Last update` = today** on any loop this meeting opened or advanced (this is the movement signal `cos-loop-closing` reads for staleness). New loops get `Opened` and `Last update` set to today.
7. **Note decisions** → `memory/episodic/decisions/` if any were made.
8. **Outward items → queue.** Any follow-up email/message is a **proposal** in `queue/outbound/` — exact text, **in the principal's voice** (load `core/voice.md` + `procedural/drafting.md`) — surfaced in the review surface. Never sent. **Fill the dashboard display fields** (`engine/templates/proposal.md`) so it renders as a rich card: `topic:` = the account/project the meeting concerns (else the meeting title); `source:` = `meeting`; `context:` = one line on what this follow-up is; `## What happened` = the meeting outcome that triggered it (decision, ask, commitment); `## Why this is in the sweep` = why it surfaced now (e.g. "you committed to send the deck", "they're waiting on pricing").

## Output
Per processed meeting: an episodic note + updated commitments/loops + any outward proposals in the queue. Routing is the point: inward facts auto-append, outward comms go to the queue. On a day with nothing to process, no output.

## Test scenarios (verification)
- A day's transcript yields an episodic note + a commitment in `state/commitments.md` + an outward draft routed to `queue/` — three targets, correct routing, capture footer appended.
- **Idempotency:** re-running over the same 24h produces **no duplicate** episodic note or re-appended commitment (already-captured meetings are skipped).
- A meeting whose transcript isn't ready is **skipped** and picked up on a later run; an empty 24h window produces **no output**.
- Resolved attendees appear as `[[entity]]` backlinks; an unknown attendee is staged for enrichment, not invented.
- The outward draft is in the principal's voice; facts derived from the transcript carry `origin: observed` and a `source` backlink.
- No outward message is sent under the default autonomy dial.

## Output contract
| Artifact | Template | Path | Required frontmatter |
|---|---|---|---|
| meeting note | `engine/templates/episodic.md` | `memory/episodic/meetings/YYYY-MM-DD-<slug>.md` | `type`, `date`, `entities`, `origin`, `sources` |
| decision note | `engine/templates/episodic.md` | `memory/episodic/decisions/YYYY-MM-DD-<slug>.md` | `type`, `date`, `entities`, `origin`, `sources` |
| outward follow-up | `engine/templates/proposal.md` | `queue/outbound/YYYY-MM-DD-<slug>.md` | `type`, `date`, `skill`, `status`, `reversibility`, `tool`, `args_digest` |
| capture footer | `engine/templates/capture-footer.md` | `log/runs/<date>-<run>.md` | (appended block) |

Commitments and loops append to `state/commitments.md` / `state/open-loops.md` (append-only tables, no frontmatter).

Migration window (`schema:` absent or < 1 in `config.md`): read both old and new frontmatter/fact-line formats, write only the new; this note retires when migration completes.

## Capture footer
End with `engine/templates/capture-footer.md`.
