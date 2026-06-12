---
name: cos-review
description: Render the pending review surface — outbound proposals, open questions, Tier-2 memory diffs — as one decision dashboard you triage by clicking, then ingest your send/edit/reject decisions back into the queue. Invoke anytime you have things to approve.
cadence: on-demand        # config.md schedules.review (optional)
kind: ritual
mutates: true             # ingest edits proposal status + appends corrections; never sends (the gate does)
---

# cos-review — the decision dashboard

> The rendered upgrade to `queue/review/`. Turns everything awaiting your decision into one
> self-contained `dashboard-<date>.html`: a tab bar (**To review · Queued · Working · Done** +
> **Prompts & sources**) of cards grouped by **topic**, each with a source·date eyebrow, headline,
> context, what-happened, an editable draft, and "why this is in the sweep". You click
> **send / edit / reject / answer**, and a persistent feedback bar lets you leave **notes** for the
> agent scoped to a card, a topic, or the whole tab. The skill routes every decision back through the
> machinery that already exists. Inspired by the "agent in the inbox, human in a shared document"
> pattern — every draft and decision stays visible in one place instead of scattered across `.md` files.
>
> **Tabs map to proposal status:** To review = `pending`, Feedback = `feedback` (you left a note;
> awaiting the agent's revision), Queued = `approved` (decided, awaiting the gate/dial),
> Working = `working` (optional in-flight transient), Done = `sent`/`rejected`. Topic comes from each
> proposal's `topic:` frontmatter (default `General`).
>
> **The dashboard never sends.** A `send` only flips a proposal to `status: approved`; the
> outbound gate (`engine/eval/hooks/outbound_gate.py`) + the autonomy dial remain the *only* path to
> a real outward call (`INSTRUCTIONS.md` §1, §4, §9). This skill is a view + a write-back loop.

Scripts live beside this file: `review_lib.py` (collect cards / parse decisions / write primitives),
`render.py` (HTML), `serve.py` (optional localhost write-back). They reuse `engine/eval/lib`
(`frontmatter`, `outbound.digest`) — the gate's own contract, not a parallel one.

## Steps

### Phase A — render
1. **Read state first** (`INSTRUCTIONS.md` §3): `state/current.md`. Resolve the instance folder
   (engine `AGENTS.md` — two roots).
2. **Serve it (default — decisions save themselves).** If you can run Python in this session — which you
   just proved by being here — start the live write-back server so **every click persists with zero export
   step**: `COS_SCRIPT_EXEC_VERIFIED=1 python serve.py <instance_dir> <YYYY-MM-DD> --open` (run it in the
   background; it blocks while serving). It renders the dashboard from the queue — `queue/outbound/*.md`
   (`status: pending`), open rows in `state/pending-questions.md`, and staged Tier-2 diffs under
   `queue/review/memory/*` (shown as the **raw diff**, never summarized) — opens
   `http://127.0.0.1:<port>/` in the browser, and appends each **send/edit/reject/answer/note** straight
   into `queue/review/decisions-<date>.jsonl` as it's clicked. The principal clicks **Done** (or you stop
   the process) when finished. Empty queue → a valid "nothing to review" page. The server is loopback-only,
   writes only under `queue/review/`, and performs **no** outward action (the gate is still the only send).
3. **Fallback — no shell / headless / scheduled run.** If Python can't run interactively here, render the
   static file instead: `render.py <instance_dir> <YYYY-MM-DD> --open` (omit `--open` for non-interactive
   runs — it just prints the path). With no server the page can't write back on its own, so the principal
   clicks **Export decisions** to save `decisions-<date>.jsonl` into `queue/review/` themselves. Use this
   path only when the server genuinely won't run; the auto-save server is the intended experience.
4. **Stop.** The principal triages on their own time. Do not proceed to ingest until decisions exist
   (the server returns when they click **Done**; the export flow, when the JSONL appears).

### Phase B — ingest (when `decisions-<date>.jsonl` is present)
5. **Parse** `review_lib.py decisions queue/review/decisions-<date>.jsonl`. Skip any `card_id` already
   recorded applied in this run's log entry (idempotent — `INSTRUCTIONS.md` §2 append-only ledger).
6. **Route each decision** (full table in `engine/templates/decision-record.md`):
   - **`send`/`approve`** → `review_lib.py set-status <proposal> approved`. Unchanged accept is
     positive signal — note it lightly, **no correction** (§4). Never send here; leave it for the gate.
   - **`edit`** → rewrite the proposal's text **and** its `json` Action block from the decision `text`,
     then `review_lib.py regen-digest <proposal>` so the gate still matches (gate KTD2). Append a
     `#voice`/`#process` correction to `state/corrections.md` (`methods/write-back.md` §2/§4).
   - **`reject`** → `set-status <proposal> rejected` + a correction.
   - **`approve`/`reject` on a `memory:` card** → `review_lib.py resolve-memory <instance_dir> <card_id> <decision>`. Approve stages the diff in `queue/review/memory/approved/` for the **next `cos-consolidate-memory` run to apply** (only the cold path may edit memory — the dashboard never does); reject archives it to `…/rejected/`. A reject is also a correction.
   - **`answer`** → `review_lib.py resolve-question <state/pending-questions.md> <card_id> answer --answer "<text>" --ts <iso>` — it flips the row's Status to `answered` and logs the answer under `## Answers` for the owning skill to pick up next sweep; the row leaves **To review** for **Done**.
   - **`dismiss`** → `review_lib.py resolve-question <state/pending-questions.md> <card_id> dismiss` — marks the row `dismissed` (no answer logged).
   - **`note`** (free-text feedback, `scope: card|topic|all`) → for each proposal in the note's scope
     (the one card, every proposal in `topic:<name>`, or all in `all:<tab>`), record it durably with
     `review_lib.py note <proposal> "<text>" --ts <iso>` — which appends to the proposal's `## Notes`
     and flips its status to `feedback` so it leaves **To review** for the **Feedback** tab. When a note
     states a durable preference ("always route X to Y", "never reply on weekends") also append a
     `#voice`/`#process`/`#priority` correction. Notes are additive — process every note row.

### Phase C — revise from feedback and re-present
8. For each proposal with **`status: feedback`**, read its `## Notes`, then **revise** the draft + the
   `json` Action block to satisfy the feedback and run `review_lib.py regen-digest <proposal>` so the
   gate still matches (KTD2). Append a `#voice`/`#process` correction for any durable preference the
   feedback expressed. Then **re-present**: `review_lib.py set-status <proposal> pending` (back to
   **To review** with the revision visible) — or `approved` if the feedback said "send it". Leave the
   `## Notes` as the trail. This is the loop: feedback captured → item revised → re-surfaced.

### Close
9. **Capture + close** (`INSTRUCTIONS.md` §3): append the capture footer (`engine/templates/capture-footer.md`)
   with the applied `card_id`s as the ledger, then rewrite `state/current.md`.

## Output

`queue/review/dashboard-<date>.html` (the rendered surface) and, after ingest, updated proposal
`status:` + any corrections — plus the capture footer + refreshed `state/current.md`. No outward
action is ever taken by this skill.

## Test scenarios (verification)
- A queue with N pending proposals + M open questions + K Tier-2 diffs renders one
  `dashboard-<date>.html` with three sections and correct counts; the file references **no** external
  network resource; a memory card shows the literal diff.
- Choosing **send** sets that proposal's `status: approved` and performs **no** outward action; the
  gate/dial still governs the eventual send.
- Choosing **edit** rewrites the proposal text + Action block, regenerates `args_digest`, and appends
  a `#voice`/`#process` correction; the new digest matches the rewritten block (the gate would accept).
- Choosing **reject** sets `status: rejected` + a correction; an unchanged **send** appends no correction.
- On a host **without** verified `script_exec`, the export-file flow is used; ingesting the exported
  JSONL is identical to the live-server path.
- Re-running ingest applies no decision twice (idempotent ledger).

## Output contract
| Artifact | Template | Path | Required frontmatter |
|---|---|---|---|
| decision dashboard | `engine/skills/cos-review/render.py` | `queue/review/dashboard-YYYY-MM-DD.html` | (HTML, not frontmatter) |
| decision records | `engine/templates/decision-record.md` | `queue/review/decisions-YYYY-MM-DD.jsonl` | (JSONL, one object per line) |
| correction (on edit/reject) | `engine/templates/capture-footer.md` corrections schema | `state/corrections.md` | (appended record) |
| capture footer | `engine/templates/capture-footer.md` | `log/runs/<date>-<run>.md` | (appended block) |
