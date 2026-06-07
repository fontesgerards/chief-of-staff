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
2. **Ingest the record.** Transcript/notes via the **read-only extractor** (`cos-extract-from-sources`) → staging. Do not write memory directly from raw source.
3. **Resolve attendees & accounts.** Match the meeting to its calendar event and resolve speakers/attendees against `semantic/` (people/accounts) so the episodic note's `entities` backlinks connect. Unknown attendees → stage for `cos-entity-enrichment`; don't invent.
4. **Capture outcomes → episodic.** Write `memory/episodic/meetings/YYYY-MM-DD-<slug>.md` (derived, restated — not verbatim) with resolved `[[entity]]` backlinks.
5. **Extract commitments → state.** Append to `state/commitments.md` (who/what/due/source).
6. **Open/close loops → state.** Update `state/open-loops.md`.
7. **Note decisions** → `memory/episodic/decisions/` if any were made.
8. **Outward items → queue.** Any follow-up email/message is a **proposal** in `queue/outbound/` — exact text, **in the principal's voice** (load `core/voice.md` + `procedural/drafting.md`) — surfaced in the daily brief. Never sent.

## Output
Per processed meeting: an episodic note + updated commitments/loops + any outward proposals in the queue. Routing is the point: inward facts auto-append, outward comms go to the queue. On a day with nothing to process, no output.

## Test scenarios (verification)
- A day's transcript yields an episodic note + a commitment in `state/commitments.md` + an outward draft routed to `queue/` — three targets, correct routing, capture footer appended.
- **Idempotency:** re-running over the same 24h produces **no duplicate** episodic note or re-appended commitment (already-captured meetings are skipped).
- A meeting whose transcript isn't ready is **skipped** and picked up on a later run; an empty 24h window produces **no output**.
- Resolved attendees appear as `[[entity]]` backlinks; an unknown attendee is staged for enrichment, not invented.
- The outward draft is in the principal's voice; facts derived from the transcript carry `origin: observed` and a `source` backlink.
- No outward message is sent under the default autonomy dial.

## Capture footer
End with `engine/templates/capture-footer.md`.
