---
name: meeting-follow-up
description: After a meeting, capture outcomes into memory, extract commitments, and draft any follow-up messages as proposals for your approval. Invoke after a call or when a new transcript lands.
cadence: on-demand        # triggered after a meeting / new transcript
kind: ritual
---

# meeting-follow-up — close the loop after a meeting

> Where the three write-targets meet in one run (a clean demonstration of inward-vs-outward, `INSTRUCTIONS.md` §2). Absorbs the old standalone "to-do extraction." Load `procedural/meeting-follow-up.md` first.

## Steps
1. **Ingest the record.** Transcript/notes via the **read-only extractor** (`extract-from-sources.md`) → staging. Do not write memory directly from raw source.
2. **Capture outcomes → episodic.** Write a `memory/episodic/meetings/YYYY-MM-DD-<slug>.md` (derived, restated — not verbatim).
3. **Extract commitments → state.** Append to `state/commitments.md` (who/what/due/source).
4. **Open/close loops → state.** Update `state/open-loops.md`.
5. **Outward items → queue.** Any follow-up email/message is a **proposal** in `queue/outbound/` (exact text), surfaced in the daily brief. Never sent.
6. **Note decisions** → `memory/episodic/decisions/` if any were made.

## Output
Episodic note + updated commitments/loops + outward proposals in the queue. Routing is the point: inward facts auto-write (append-only), outward comms go to the queue.

## Test scenarios (verification)
- A transcript yields an episodic note + a commitment in `state/commitments.md` + an outward draft routed to `queue/` — three targets, correct routing, capture footer appended.
- Facts derived from the transcript carry `origin: observed` and a `source` backlink.
- No outward message is sent under the default autonomy dial.

## Capture footer
End with `engine/templates/capture-footer.md`.
