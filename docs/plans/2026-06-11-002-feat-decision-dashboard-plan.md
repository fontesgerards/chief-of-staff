---
title: "feat: decision dashboard — a rendered review surface over the queue"
type: feat
status: completed
date: 2026-06-11
depth: deep
---

# feat: decision dashboard — a rendered review surface over the queue

## Summary

Give the principal a single **rendered artifact** to triage what the system wants to do — outbound proposals, pending questions, and Tier-2 memory diffs — instead of reading and hand-editing scattered Markdown files. Inspired by Dan Shipper's Codex inbox workflow (one shared document per run, every draft/decision surfaced as a card, the human replies inline, the agent waits before sending). The artifact is a self-contained `dashboard-<date>.html` generated from the existing queue; the principal clicks **send / edit / archive / reject / answer** per card; decisions round-trip back as an append-only `decisions-<date>.jsonl`; a new `/cos-review` skill ingests them and routes each through machinery that already exists — flipping a proposal to `approved` (the `outbound_gate.py` still does the only real sending), recording a `#`-tagged correction on an edit, or rejecting. No change to the safety contract; this is a view + write-back path, additive over `engine/templates/proposal.md`, `engine/eval/hooks/outbound_gate.py`, and the corrections loop.

## Problem Frame

`INSTRUCTIONS.md` §1 already names `instance/queue/review/review-<date>.md` "the single approval surface," and `queue/review/README.md` already says it is for outbound proposals + Tier-2 memory diffs + pending questions, and that "v1 is a plain Markdown file. It can be upgraded to a live artifact later without changing the loop." That upgrade has not been built. Today the principal must open `queue/outbound/*.md` files individually, read prose, and hand-edit frontmatter `status:` — there is no consolidated, scannable surface and no structured way for the system to pick up the resulting decisions. The decision *machinery* is complete (proposal template with machine-readable Action block + `args_digest`, the payload-bound `PreToolUse` gate, corrections-drive-learning in §4, cold-path consolidation); what is missing is the **ergonomic layer** the video demonstrates: cards in one place, one-gesture decisions, and an ingestion step that turns those gestures back into the queue state the machinery reads. The runtime is heterogeneous (Claude Code, Cowork app-open, Codex) and script-exec / long-running processes are not guaranteed, so the surface must degrade gracefully and fail closed.

---

## Requirements

- R1. One generated artifact per review run, `instance/queue/review/dashboard-<date>.html`, self-contained (inlined CSS/JS, **zero external/network dependencies**), openable by double-click on any OS.
- R2. The dashboard surfaces all three decision classes the review surface owns: **outbound proposals** (from `queue/outbound/*.md`, `status: pending`), **pending questions** (`state/pending-questions.md`), and **Tier-2 memory diffs** (shown as the **raw diff**, never a summary — a benign-looking malicious write must not slip through, per `queue/review/README.md`).
- R3. Per-card decisions map 1:1 to a decision the agent could also apply by hand (agent-native parity): outbound → `send` (approve as-is) · `edit` (revise text) · `reject`; question → `answer` (free text) · `dismiss`; memory diff → `approve` · `reject`.
- R4. **The dashboard never sends.** A `send`/approve decision only sets the proposal's `status: approved`; the existing `outbound_gate.py` + autonomy dial remain the sole path to an actual outward tool call. The safety floor (`INSTRUCTIONS.md` §9) is unchanged.
- R5. Decisions round-trip via one append-only format, `instance/queue/review/decisions-<date>.jsonl`, regardless of how they were produced (manual export or live server) — append-only matches the inward-write ethos (§2): nothing is destroyed, so a bad write can't silently corrupt state.
- R6. **Write-back is runtime-aware and fail-closed.** Default (works everywhere, no process): the dashboard collects decisions in-page and an **Export** button downloads `decisions-<date>.jsonl`. When `script_exec` is verified for the live host (config.md runtime row), the skill may launch a stdlib-only localhost server that writes each decision directly. Neither path ever performs an outward action.
- R7. `/cos-review` ingests `decisions-<date>.jsonl` and routes each: `send`/approve → proposal `status: approved`; `edit` → append a `#voice`/`#process`-tagged **correction** (`state/corrections.md`, per `write-back.md` §2/§4) **and** redraft the proposal text + regenerate `args_digest` so the gate still matches; `reject`/`dismiss` → `status: rejected` / question status `dismissed`; `answer` → record the answer for the relevant skill and close the question. Each ingested decision is idempotent (re-running ignores already-applied lines).
- R8. Edits and rejects feed learning: an `edit` or `reject` is a correction (§4); an unchanged `send`/approve is positive signal noted lightly, **not** a correction (§4 final sentence).
- R9. Pure stdlib Python (matches `engine/eval/`), no new dependencies; reuses `engine/eval/lib/frontmatter.py` and `engine/eval/lib/outbound.py` (`digest`, canonicalization) rather than reimplementing.
- R10. Documented surface: `INSTRUCTIONS.md` §1 and `queue/review/README.md` updated to describe the rendered artifact + decision round-trip; glossary entry; the skill carries an output-contract table like every other skill.

---

## Key Technical Decisions

- **KTD1 — The dashboard is a derived, ephemeral view; Markdown proposals stay canonical.** The HTML is regenerated from the queue and is never authoritative. This keeps every decision a git-diffable change to `queue/outbound/*.md` + `corrections.md`, preserving the "brain is plain Markdown, every change is a reviewable diff" invariant. *Consequence:* the dashboard can be deleted/regenerated freely; truth lives in the queue.
- **KTD2 — One decision format, two producers.** `decisions-<date>.jsonl` is the only contract between surface and ingest. The Export button and the optional server both emit the identical line shape, so the ingest phase (R7) is agnostic to write-back mechanism. *Consequence:* runtimes without script-exec lose live round-trip but keep full functionality via export.
- **KTD3 — Approve flips status only; the gate is still the gate (R4).** Mirrors `outbound_gate.py` KTD5: `status: approved` makes a proposal *eligible*; the autonomy dial + payload-bound digest match are what actually permit execution. The dashboard deliberately cannot short-circuit this — there is no code path from a click to an MCP call.
- **KTD4 — Edit regenerates the digest, by design.** An `edit` decision rewrites the proposal's human text *and* its Action block, then recomputes `args_digest` via `engine/eval/lib/outbound.py:digest`. Without regeneration the gate would (correctly) refuse the edited send as drift (gate KTD2). So the ingest step owns digest regeneration, keeping edited sends executable.
- **KTD5 — Server is localhost-only, single-run, no framework.** When used, `serve.py` binds `127.0.0.1` on an ephemeral port, serves exactly the one dashboard, accepts `POST /decision` appending to the JSONL, and exits on `/done` or SIGINT. stdlib `http.server` only. It performs **no** outward calls and touches only `queue/review/`. Absence of the server is a supported, documented mode — not a failure.
- **KTD6 — Raw diff for memory, never a summary (R2).** Tier-2 memory cards embed the literal diff text in a `<pre>`; the dashboard does not paraphrase. This carries the `queue/review/README.md` security rationale into the rendered surface.
- **KTD7 — Idempotent, append-only ingest (R5/R7).** Each decision line carries a stable `card_id`; ingest records applied ids in the run log and skips lines already applied, so re-running `/cos-review` after a partial session is safe.

---

## Implementation Units

### U1. Decision record schema + card model
- **Goal:** define the append-only `decisions-<date>.jsonl` line and the in-memory card the renderer/ingest share.
- **Requirements:** R3, R5, R7, KTD2, KTD7.
- **Files:** `engine/templates/decision-record.md` (schema doc + example), shared parsing in `engine/skills/cos-review/review_lib.py` (create).
- **Approach:** one JSON object per line: `{card_id, kind: outbound|question|memory, source, decision: send|edit|reject|answer|dismiss|approve, text?, ts}`. `card_id` is `<kind>:<slugged-source>` — stable across regenerations of the same pending item. `review_lib.py` exposes `collect_cards(instance_dir) -> [Card]` (reads pending proposals via `frontmatter`, pending-questions table, staged Tier-2 diffs) and `parse_decisions(path) -> [Decision]`.
- **Test scenarios:** a pending proposal + a question + a memory diff yield three cards with stable ids; re-collecting yields identical ids; a malformed JSONL line is skipped with a warning, not a crash.
- **Verification:** `review_lib` round-trips card → decision → card_id match.

### U2. Dashboard renderer
- **Goal:** `render.py` turns collected cards into one self-contained `dashboard-<date>.html`.
- **Requirements:** R1, R2, R3, R6, KTD1, KTD6.
- **Dependencies:** U1.
- **Files:** `engine/skills/cos-review/render.py` (create).
- **Approach:** stdlib only; build the HTML string with inlined `<style>`/`<script>`. Three sections (Outbound / Questions / Memory Δ) with a count each. Each card shows: title, what/to-whom, exact text (editable `<textarea>` for outbound, `<pre>` raw diff for memory), reversibility badge, and decision controls (R3). All decisions accumulate in a JS array; an **Export decisions** button serializes to `decisions-<date>.jsonl` via a Blob download. A small banner shows whether a live write-back server is present (set by U3) and, if so, POSTs each decision on click in addition to buffering it. HTML-escape all card content. Empty queue → a "nothing to review" page, still valid.
- **Test scenarios:** snapshot of a 3-card dashboard contains no `http://`/`https://` external refs; memory card contains the literal diff; outbound text is HTML-escaped; empty input renders the empty state.
- **Verification:** open generated file in a browser, all three sections render, Export downloads valid JSONL.

### U3. Optional localhost write-back server
- **Goal:** `serve.py` serves the dashboard and persists clicks live when the runtime allows.
- **Requirements:** R5, R6, KTD2, KTD5.
- **Dependencies:** U2.
- **Files:** `engine/skills/cos-review/serve.py` (create).
- **Approach:** stdlib `http.server.ThreadingHTTPServer` bound to `127.0.0.1:0` (ephemeral port). `GET /` → the rendered dashboard (with the server banner enabled). `POST /decision` → validate JSON, append one line to `decisions-<date>.jsonl`, return 204. `POST /done` → flush + shutdown. Prints the chosen `http://127.0.0.1:<port>/` URL on stdout for the skill to relay. No outward network; binds loopback only. Hard refuse to start if invoked on a host whose config row lacks verified `script_exec` (skill enforces; server also self-checks an env flag).
- **Test scenarios:** POST a decision → line appended; POST /done → process exits; binding is loopback-only; malformed POST body → 400, no write.
- **Verification:** `curl` a decision to the running server writes exactly one JSONL line; `/done` stops it.

### U4. `/cos-review` skill (render → serve → ingest)
- **Goal:** the orchestration skill the principal invokes.
- **Requirements:** R4, R6, R7, R8, R10, KTD3, KTD4, KTD7.
- **Dependencies:** U1–U3.
- **Files:** `engine/skills/cos-review/SKILL.md` (create).
- **Approach:** **Phase A (render):** read state first (§3), `collect_cards`, run `render.py`, write `dashboard-<date>.html`; if the live host's config row has verified `script_exec`, offer to launch `serve.py` and relay the localhost URL; else instruct the export flow. **Phase B (ingest):** read `decisions-<date>.jsonl`, skip already-applied `card_id`s (run-log ledger, KTD7), and for each: `send`/`approve` → set proposal `status: approved` (note positive signal lightly, R8 — no correction); `edit` → rewrite proposal text + Action block, regenerate `args_digest` via `outbound.py:digest` (KTD4), append a correction (`#voice`/`#process`, R8); `reject` → `status: rejected` + correction; `answer` → record the answer + mark question resolved; `dismiss` → question `dismissed`. Never send — approved proposals are left for the gate/dial (R4). Append the capture footer; rewrite `state/current.md` (§3).
- **Test scenarios:** the five SKILL "Test scenarios" lines below; plus: an `edit` decision produces a proposal whose new `args_digest` matches its rewritten Action block (gate would accept); a re-run ingests nothing new (idempotent).
- **Verification:** end-to-end — render a 3-card dashboard, export decisions for one send / one edit / one reject, ingest, and confirm queue + corrections reflect exactly those three with no outward call.

### U5. Tests
- **Goal:** deterministic coverage for the lib, renderer, and server.
- **Files:** `engine/skills/cos-review/test_review_lib.py`, `test_render.py`, `test_serve.py` (create) — or colocated under `engine/eval/` if that better matches the harness; decide at build.
- **Approach:** pytest, stdlib + existing `engine/eval` fixtures. Cover U1–U3 scenarios above.
- **Verification:** `pytest engine/skills/cos-review/` (or the chosen path) green.

### U6. Documentation + wiring
- **Goal:** make the surface discoverable and contractual.
- **Requirements:** R10.
- **Files:** `engine/INSTRUCTIONS.md` §1 (modify — name the rendered artifact + round-trip), `instance/queue/review/README.md` (modify), the glossary template (add `decision dashboard` / `decisions.jsonl`), `engine/skills/cos-review/SKILL.md` output-contract table, `config.md` `delivery.review` mention if relevant.
- **Verification:** §1 and README describe render → decide → ingest; glossary defines the new terms; skill lists its output contract like peers.

---

## Test scenarios (skill-level, for SKILL.md)

- A queue with N pending proposals + M questions + K Tier-2 diffs renders one `dashboard-<date>.html` with three sections and correct counts; no external network references.
- Choosing **send** on a card sets that proposal's `status: approved` and performs **no** outward action; the gate/dial still governs the eventual send.
- Choosing **edit** rewrites the proposal text + Action block, regenerates `args_digest`, and appends a `#voice`/`#process` correction.
- Choosing **reject** sets `status: rejected` and appends a correction; an unchanged **send** appends **no** correction (positive signal only).
- On a host without verified `script_exec`, the skill uses the export-file flow (no server); ingest of the exported JSONL is identical to the live-server path.
- Re-running ingest after a partial session applies no decision twice (idempotent).

---

## Scope Boundaries

- **In:** rendered HTML review surface; export + optional localhost write-back; `/cos-review` skill; ingest routing into existing proposal/correction machinery; docs.
- **Out (this PR):** real-time collaborative editing / hosted Proof-style sync; mobile UI; auth on the local server (loopback-only is the boundary); auto-send at any dial (the gate owns that); changing the proposal/gate/correction contracts themselves; an email-specific "inbox sweep" skill (the dashboard is connector-agnostic — email cards are just outbound proposals like any other).
- **Deferred:** a `delivery.review` channel that pushes the dashboard to an external surface; richer card types (calendar conflicts, digests); a Proof/HTML toggle.

---

## Addendum — structure pass (2026-06-11)

Second iteration, modeled on Dan Shipper's review UI, layered on the same queue/gate/corrections machinery:

- **Tabs** mapped to proposal status: To review = `pending`, Queued = `approved`, Working = `working` (optional transient), Done = `sent`/`rejected`; questions and memory bucket by resolution. Counts always shown (incl. 0), faithful to the reference.
- **Topic grouping** from each proposal's optional `topic:` frontmatter (default `General`); questions → "Questions", memory → "Memory".
- **Richer cards**: source·date eyebrow, serif headline, context lede, "What happened", collapsible "Read full source", editable draft, "Why this is in the sweep" bullets — parsed tolerantly from `## headings` / `**bold labels**` / the Action JSON, with `proposal.md` extended (optional `topic`/`source`/`context` frontmatter + `## What happened` / `## Why this is in the sweep` sections), backward-compatible.
- **Floating feedback bar** (`note` decision): "Talking to: <scope>" with Broader/Narrower scope (card → topic → everything-in-tab) and ↑/↓ (move between items) · ⌘↑/↓ (change scope) · Enter (send) keys. Notes are additive; ingest applies them as agent guidance and promotes durable ones to corrections.
- **Design** (ce-frontend-design): editorial — warm paper palette, transitional-serif headlines, uppercase letterspaced micro-labels, one indigo accent rail + amber focus pill, sticky blurred tab/feedback bars, light+dark via `prefers-color-scheme`. Visually verified via `agent-browser` screenshots (To review + Queued tabs).
- **Scope is color-coded** (narrow→wide = indigo→teal→amber): the in-scope cards' rail + faint tint, the "Talking to" pill, the SCOPE label, and the input's left rail all read a single `--scope` variable set by a `body.scope-*` class; the focused item keeps a thicker rail so it stays distinguishable inside a wider scope. Scope buttons disable at the ends (Broader at widest, Narrower at narrowest / when no card is focused).

## Addendum — feedback loop (2026-06-11)

Closes the human↔agent loop on the board:

- **New `feedback` status → "Feedback" tab** (between To review and Queued). `_STATUS_TAB` maps it; `set_status`/`add_note` accept it.
- **`add_note(proposal, text, ts)`** appends to a `## Notes` section (newest-first, created if absent) and flips the proposal to `feedback`. `_outbound_fields` parses `## Notes` into `fields.notes`, rendered as a "Your feedback" block (amber accent) with an "Awaiting the agent's revision" line; feedback cards show **no action buttons** (they await the agent).
- **In-session**: sending a note attaches it to every in-scope card (`sessionNotes`), which immediately shows the feedback and moves the card to the Feedback tab (`effectiveTab`), with live tab-count updates — no round-trip needed to see it.
- **Durable round-trip** (`/cos-review` ingest): a `note` decision runs `review_lib.py note <proposal> "<text>"` per in-scope proposal (Phase B). **Phase C — revise from feedback**: for each `status: feedback` proposal, the agent reads `## Notes`, revises the draft + Action block, regenerates the digest, records durable preferences as corrections, then re-presents (`set-status … pending`) so the revised item returns to To review. Loop: feedback captured → item revised → re-surfaced.
- Verified via `agent-browser`: a durable-feedback card loads in the Feedback tab with its note; adding a note in-session moves a card from To review (2→1) to Feedback (1→2) with the note shown.

## Addendum — producers emit rich cards (2026-06-11)

The two skills that write outbound proposals now populate the dashboard display fields so real cards render as richly as the mockups:

- **`cos-meeting-follow-up`** (step 8): `topic:` = account/project (else meeting title), `source: meeting`, `context:`, `## What happened` (the meeting outcome that triggered it), `## Why this is in the sweep` (e.g. "you committed to send the deck").
- **`cos-loop-closing`** (step 3): `topic:` = the loop's account/project (else bucket), `source: loop`, `context:`, `## What happened` (owner-less / no movement since `Last update` / past `Due`), `## Why this is in the sweep` (the staleness/ownership trigger).
- Display fields stay **optional** in `proposal.md` (gate-required keys unchanged), so older proposals still render with graceful fallbacks. Verified: a proposal in the new shape parses to a full card (topic, MEETING eyebrow, context, what-happened, why bullets, draft).

## Addendum — Memory Δ loop wired to the cold path (2026-06-11)

The **Memory Δ** cards now populate and round-trip, completing the third decision class:

- **Stage** — `cos-consolidate-memory` writes each Tier-2 memory proposal as an individual raw-diff file `queue/review/memory/<date>-<slug>.diff` (its canonical staging), which the dashboard renders as a Memory Δ card (raw diff, never summarized).
- **Resolve** — the dashboard's approve/reject routes through a new `review_lib.resolve_memory(instance, card_id, decision)` (+ CLI `resolve-memory`): approve → `queue/review/memory/approved/`, reject → `…/rejected/`. Non-recursive collect means resolved diffs leave the board. The dashboard **never edits memory**.
- **Apply** — `cos-consolidate-memory` consumes `…/approved/*.diff` as its first destructive step (inside the git-commit/snapshot-first review-surface branch), applies each to its target file, changelogs "approved via dashboard", and deletes it. Idempotent (a gone diff no-ops); rejected diffs are never applied.
- Loop: cold path **stages** → dashboard **approves** → cold path **applies**. Verified via CLI: staged diff → Memory card → approve → moved to `approved/`, off the board, awaiting apply. 126 tests pass.
