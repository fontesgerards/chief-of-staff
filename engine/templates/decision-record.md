# Decision record — `queue/review/decisions-<date>.jsonl`

> The **append-only** round-trip format between the rendered decision dashboard and
> the `/cos-review` ingest phase. One JSON object per line. **By default** each line is
> written automatically by the localhost write-back server as the principal clicks —
> no manual step. On a host that can't run the server (headless / no shell), the
> dashboard's **Export decisions** button produces the identical file as a fallback.
> Both emit the same shape, so ingest is agnostic to how a line got here.
>
> Append-only matches the inward-write ethos (`INSTRUCTIONS.md` §2): nothing is
> destroyed, so a bad or duplicate decision can't silently corrupt the queue.
> Ingest is idempotent — each `card_id` is applied once (the run log is the ledger).

## Line schema

```json
{
  "card_id": "outbound:2026-06-11-reply-tony",
  "kind": "outbound",
  "source": "queue/outbound/2026-06-11-reply-tony.md",
  "decision": "send",
  "text": "optional — revised draft (edit) or answer text (answer)",
  "ts": "2026-06-11T14:32:00Z"
}
```

| Field | Meaning |
|---|---|
| `card_id` | for an action: `<kind>:<stable-slug>` (the idempotency key, survives regeneration). For a `note`: the **target** — a card id, `topic:<name>`, or `all:<tab>`. |
| `kind` | `outbound` \| `question` \| `memory` (omitted on `note`). |
| `source` | relative path / identifier the card came from. |
| `decision` | `send`/`approve`, `edit`, `reject`, `answer`, `dismiss`, or `note` (free-text feedback). |
| `text` | revised draft (`edit`), the answer (`answer`), or the feedback (`note`). |
| `scope` | `note` only: `card` \| `topic` \| `all` — how wide the feedback applies. |
| `tab` | `note` only: which board tab it was raised from. |
| `ts` | ISO-8601 timestamp the decision was made. |

### Notes (the floating feedback bar)

A `note` is free-text guidance the principal aims at a card, a topic, or everything in a tab —
the persistent bottom bar in the dashboard ("Talking to: …", Broader/Narrower scope). It is
**additive** (many notes may target the same card), unlike actions (one per card; the latest wins).

On ingest, each proposal in the note's scope gets the text appended to its `## Notes` section and its
status flipped to `feedback` — moving it to the **Feedback** tab until the agent's next pass revises
the draft to satisfy the feedback and re-presents it (back to **To review**). The dashboard also shows
the feedback inline on the card immediately. The loop: feedback captured → item revised → re-surfaced.

```json
{"card_id": "topic:Sponsorships", "decision": "note", "scope": "topic", "tab": "review",
 "text": "route all unknown sponsorship asks to Sydney unless already picked up", "ts": "2026-06-11T14:40:00Z"}
```

## How ingest routes each decision (`/cos-review` Phase B)

- **`send` / `approve`** → set the proposal's `status: approved` (the outbound gate + autonomy dial
  still govern the actual send — the dashboard never sends). Unchanged accept = positive signal,
  **no** correction (`INSTRUCTIONS.md` §4).
- **`edit`** → rewrite the proposal's text + Action block from `text`, **regenerate `args_digest`**
  (`review_lib.py regen-digest`) so the gate still matches, and append a `#voice`/`#process`
  correction (`state/corrections.md`).
- **`reject`** → `status: rejected` + a correction.
- **`answer`** → `review_lib.py resolve-question <state/pending-questions.md> <card_id> answer --answer "<text>"`:
  flips the row's Status to `answered` and logs the answer under `## Answers` for the owning skill to pick
  up next sweep. The question card moves to **Done**.
- **`dismiss`** → `review_lib.py resolve-question … dismiss`: marks the row `dismissed` (no answer logged).

> **Where questions come from.** Sweep skills (`cos-meeting-follow-up`, `cos-loop-closing`,
> `cos-inbox-sweep`, `cos-calendar-audit`, …) emit a genuine uncertainty *by exception* via
> `review_lib.py add-question`, which appends an open row to `state/pending-questions.md`. The dashboard
> renders each open row as an answerable card in **To review**, so the principal resolves it in the same
> pass as their sends — no separate channel.

### Question hygiene — every emitter owns its rows

With several skills emitting questions, three conventions keep the table sane (no schema change):

1. **Deterministic, key-first question text.** `add-question`'s identity (and dedup) is the first
   **48 slugified characters** of the question text. Emitters whose findings recur across overlapping
   windows (e.g. the calendar audit's daily 4-day scan) lead with a literal key —
   `[audit <YYYY-MM-DD> <check-code> <slug>] <question>` — so the unique part lands inside that
   window: idempotent across runs and phrasing drift, while two different findings on the same item
   stay distinct. Never lead with a long free-text title. Key parts must themselves be deterministic:
   date = the **finding's** date (never the run date); event slugs lead with the start time (`HHMM-…`)
   so truncated titles can't collide; day-level findings use a fixed literal (the emitting skill
   defines the exact parts — see `cos-calendar-audit` step 6).
2. **The `card_id` is derivable.** `question:<slug(question)[:48]>` — or read it back from
   `review_lib.py collect`. That id is what `resolve-question` matches on.
3. **Emitters dismiss their own expired rows.** A finding tied to a date (a Tuesday conflict) is noise
   once the date passes: each run opens by dismissing its own out-of-date open rows
   (`resolve-question … dismiss`) before emitting new ones. An emitter that consumes answers
   (calendar-audit) also dismisses the answered row after acting on it — answered → dismissed is the
   "consumed" state.
