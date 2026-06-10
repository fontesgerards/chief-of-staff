# Outward-Action Gate — structural enforcement of propose-never-act

**Date:** 2026-06-10
**Status:** Requirements (pre-planning)
**Scope tier:** Deep — feature

## Problem

`INSTRUCTIONS.md` §1 — *"anything that touches the outside world is a proposal, not an action"* — is the system's flagship rule, and today it has **no structural enforcement**. Every other safety-critical rule has a structural guard:

- The extractor is sandboxed read-only (`docs/write-isolation-config.md`) — it *physically cannot* write memory.
- `core/` edits and fact provenance are guarded by the `PostToolUse` hook `engine/eval/hooks/provenance_check.py`.

But the outward side relies entirely on the model reading §1 and *choosing* to write a proposal file instead of calling a mutating connector tool (`create_event`, a send, a post). The moment a write OAuth scope is granted — so the agent *can* execute approved sends — nothing structurally ties an outward tool call to an approved proposal. An ordinary mistake, or an injected instruction, can act outward directly.

`write-back.md` §8.2 states the relevant design creed: *"you can't scan your way out — classifiers catch only 27–37% of injections, so the defense is structural; the content scan is the last, weakest layer."* A secondary **agent** reviewer is a scan. The deterministic question "was this outward action backed by an approved proposal?" deserves a deterministic, structural answer.

## Goal

Close the outward enforcement gap with a **structural gate**, not an LLM reviewer: deny any outward tool call unless (a) the autonomy dial permits that class **and** (b) a matching approved proposal exists in `instance/queue/outbound/`. This is the outward twin of `provenance_check.py`.

## Non-goals

- A secondary LLM/agent reviewer of actions. Explicitly rejected per §8.2 — it is probabilistic, adds latency, and is itself an injection target. (Revisit only if payload canonicalization proves too brittle; see Outstanding Questions.)
- Implementing the read-only OAuth scope posture (layer 1) or the OS sandbox network/exec deny (layer 3). Both are **required companions** named below, but they already exist as patterns (`connectors.md`, `write-isolation-config.md`) and are not built here.
- Changing the autonomy dial model or the inward (memory) guards.

## Approach (decided)

A **`PreToolUse` gate** — preventive, not corrective. Outward sends are frequently irreversible, so a `PostToolUse` check (like the provenance hook) is too late; the call must be blocked *before* it executes.

**Matching: payload-bound (option B).** The proposal declares the exact action in a machine-readable block (tool + canonicalized args / a digest). On the live call, the gate canonicalizes `tool_input` and compares against the approved proposal. **One approval authorizes exactly one action**; any edit to recipient, text, or time fails the match and re-queues. Presence-only matching (any approved proposal of the class → allow) was rejected as too coarse — it permits replay and drift, the exact failures the gate exists to stop.

**Irreversible actions additionally require a single-use token (option C, narrowed).** For proposals marked `reversibility: irreversible`, approval mints a single-use token bound to the payload digest; the gate verifies and **consumes** it, so an identical payload cannot be sent twice. Reversible actions use B alone.

**Default-on, fail-closed.** `cos-onboarding` wires the gate into the instance's `.claude/settings.json` (it already detects-or-asks the runtime — KTD-5 in `connectors.md`). If config or the queue can't be read or parsed, the gate **denies**. The flagship rule is enforced out of the box, not opt-in. (Contrast the provenance hook, which ships as `settings.example.json` for manual wiring — the outward rule is too important to leave dark until the user acts.)

## Cross-platform enforcement — the principle is portable, the hook is not

A `PreToolUse` hook is a Claude Code construct. The **invariant** to enforce everywhere is the principle — *no outward action without an approved proposal* — using the strongest mechanism each surface offers. Three layers, three enforcement stories:

| Layer | Mechanism | Claude Code CLI | Cowork | Codex |
|---|---|---|---|---|
| **1. Read-only OAuth scopes** | enforced at the *provider*, not the harness | ✅ | ✅ **primary posture** | ✅ |
| **2. Per-proposal payload-bound gate (B)** | `PreToolUse` hook runs the queue-match | ✅ full | ⚠️ likely, **unverified** | ❌ no hook → approval-policy (coarse) |
| **3. Bash-egress deny** | OS sandbox network/exec | ✅ | ⚠️ unverified | ✅ (`network.enabled = false`) |

- **Claude Code CLI** — reference implementation. Hook fires, runs the payload-match, `exit 2` denies. Full B; sandbox closes the Bash hole.
- **Cowork** — read-only / write choice happens at the OAuth consent screen, so **layer 1 carries the weight**: connect read-only → the agent can't mutate → propose-never-act holds *by capability*. The agent drafts; the principal executes. The hook may also fire (same engine) but is unverified, so guidance is **"keep outward connectors read-only on Cowork"** rather than depending on the gate. (Matches the `write-isolation-config.md` Cowork caveat.)
- **Codex** — no pre-tool hook, so automated B isn't achievable the same way. Analog: the **permissions-profile system** (`config.toml`) + **approval policy** — a restricted acting-profile that either doesn't expose the mutating MCP server or requires per-tool human approval. Codex **fails closed**. What you get is *read-only scopes + human-approval* — a **coarser** gate that confirms "a human approved this call" but not "this payload == the approved payload." Whether Codex can run a pre-tool script is a **verify-at-build (KTD-7)** item, not asserted here.

**Design consequence — stated as a non-promise:** payload-bound matching (B) is a **Claude Code capability, not a cross-platform guarantee.** On surfaces without a pre-tool hook, the enforced floor degrades gracefully to **read-only scopes + a human-approval gate** — still propose-never-act, just without the automated fine-grained match. The doc must not claim B works everywhere.

## The honest limit — the gate is necessary, not sufficient

A tool-name gate watches **MCP tools**. It does **not** watch `Bash` — `curl`, `osascript`, `gcloud` are outward egress that route around a tool-name matcher. The literal ask was "any action *bypassing* the rules," so the structural floor is three layers together:

1. **Read-only OAuth scopes** — the agent can't act at all (the portable floor).
2. **The PreToolUse gate** — ties each outward MCP call to an approved proposal (this doc).
3. **Sandbox network/exec deny** — blocks `Bash`-driven egress so the gate can't be sidestepped.

Shipping the gate without layers 1 and 3 leaves the Bash hole open. Planning must treat all three as the unit, even though only layer 2 is built here.

## What "outward" means (the matcher's input)

The gate intercepts **mutating** connector verbs and lets **read** verbs pass untouched:

- **Outward (gated):** `create_event` / `update_event` / `delete_event` / `respond_to_event`; any Gmail send; Drive/Dropbox `create` / `move` / `delete` / `create_shared_link`; Slack post. Anything representing the principal to another person or mutating an external system.
- **Inward (pass):** `list_*` / `get_*` / `search_*` / `read_*`. Also `create_draft` is treated as inward *only if* the draft is not auto-sent — flag for confirmation in planning.

The outward set is **config-driven** (a denylist of tool-name patterns), not hardcoded, so new connectors are covered by adding a pattern.

## Success criteria

- With a write scope granted on Claude Code CLI, a direct `create_event` call **with no matching approved proposal is denied** (`exit 2`), and the denial reason is surfaced to the model so it self-corrects into writing a proposal.
- A `create_event` whose canonicalized args **match** an `approved` proposal is **allowed**; editing any field of that proposal **fails the match**.
- An irreversible approved action cannot be executed **twice** (token consumed).
- With config or queue unreadable, **all** outward calls are denied (fail-closed).
- On Cowork with read-only scopes, the agent **cannot** mutate the calendar regardless of hook status.
- The provenance hook's inward guarantees are unchanged (no regression).

## Dependencies / assumptions

- **Assumption (verify-at-build):** Cowork honors `settings.json` hooks the same as the CLI — *unverified as of 2026-06*; the design does not depend on it (falls back to layer 1).
- **Assumption (verify-at-build):** the exact outward MCP tool names/verbs per connector — verify against the installed versions (KTD-7), as `connectors.md` already requires.
- **Open:** whether Codex exposes any pre-tool-call script hook. If not, Codex enforcement is permissions-profile + approval-policy only.
- Depends on the existing proposal template (`engine/templates/proposal.md`) — extended with the machine-readable action block.
- Depends on `cos-onboarding`'s runtime detection (KTD-5) to wire the surface-appropriate enforcement.

## Outstanding questions (for planning)

- **Canonicalization rules** for fuzzy fields — timezones in event times, whitespace/quotes in body text, recipient address normalization. The robustness of B lives here. How strict is "match"? (Too strict → legitimate sends over-block; too loose → drift slips through.)
- **Proposal ↔ call linkage:** does the agent reference a proposal id in the call, or does the gate scan the queue for any approved proposal whose digest matches? The former is simpler to match but spoofable; the latter is content-bound. Likely: digest-matched, id as a hint.
- **Token lifecycle** for irreversible actions: where the token lives, how it's minted on approval, expiry.
- **Relationship to `provenance_check.py`:** new sibling hook vs. shared lib. Both are queue/▸config-aware Python guards.
- **Does approval auto-advance `status`** (`approved` → executable) at higher dials, or does the principal always execute? The dial check and this interact.
- **Codex pre-tool hook** existence (verify-at-build) — determines whether B is reachable on Codex at all.

## Handoff

Ready for `/ce-plan`. Planning should design the three layers as a unit (build layer 2; specify the layer-1/layer-3 posture and the onboarding wiring per surface), resolve canonicalization and proposal-linkage, and produce the proposal-template extension.
