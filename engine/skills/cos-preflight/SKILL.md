---
name: cos-preflight
description: Probe what this runtime verifiably supports — git, scheduling, hooks, script exec, plugin root, connectors — and record per-runtime capability rows in config.md.
cadence: on-demand        # invoked by cos-onboarding (Step 0b); re-run standalone on any new host — that IS the upgrade path for existing instances
kind: installer
mutates: false            # writes ONLY config.md's runtime: block + the run log — never memory
---

# cos-preflight — probe the runtime, record what's true

> Capabilities are **probed, never assumed**. One row per host in `config.md`'s body `runtime:` block; every capability is tri-state — `verified` (probed OK on this host) | `unverified` (claimed/doc-derived, not probed here) | `unavailable` (probed absent, or authoritative docs say it can't work) — each with `last_verified: YYYY-MM-DD`. A capability you can't prove is a capability you don't have; honest degradation beats silent failure.

## Step 1 — Detect-or-ask the host (never infer from disk)

Use a reliable **live** signal (env var, tool namespace, harness identity). **Never infer the host from on-disk artifacts** — a Cowork session sharing a Claude-Code-style filesystem (`.mcp.json` present, `claude` on PATH) is the canonical mis-detection trap (`engine/docs/U9-connector-capability-spike.md` (a)): file presence ≠ active host. When signals are ambiguous, **ask the principal** which runtime this is (Claude Code / Cowork / Codex / Cursor). Record how in `detected_via` (`asked-principal` when asked).

## Step 2 — Probes

Run each; a thrown probe is a **result** (`unavailable`), never a hard error.

1. **git** — binary on PATH + can `git init` and commit in a throwaway temp dir. That proves the tool, not durability: on VM-backed hosts (Cowork's "home" is a session VM) whether the instance repo *survives the session* is a separate question — note it in the row, don't conflate.
2. **scheduling** — scheduling tool present, AND what are its durability/expiry semantics? Cowork scheduled tasks expire ~7 days and run only while the app is open — record that; `config.md` must never claim set-and-forget where it isn't. Record which `registered_via` vocabulary this host supports (`cron-tool | routine | scheduled-task | codex-automation | dashboard | launchd`).
3. **hooks** — `verified` ONLY via an in-session **inward canary**: a trivial write under a hook-matched path whose observable side effect (marker file / stderr) confirms the hook actually fired. **NEVER** an outward/MCP call; **never** concluded from host identity or docs alone — doc-derived knowledge yields at most `unverified` or `unavailable`. On Cowork: `unavailable` — Cowork does not fire settings.json hooks (anthropics/claude-code#63360).
4. **script execution** — `python3` present + can execute engine scripts (smoke-run one). Where `unavailable`, downstream validation reports "validation unavailable" — never an LLM approximation.
5. **plugin-root resolution** — can this session read `engine/templates/` via its plugin path (`${CLAUDE_PLUGIN_ROOT}` or equivalent)? If `unavailable`, onboarding falls back to copying the needed templates into the instance — surface the fallback, don't fail.
6. **connectors (metadata-only inventory)** — which connector tools are present/callable in this session. **NEVER read content items** (no email subjects, no event bodies, no transcripts) in this profile — tool presence is the only fact recorded. Content-level classify-probes belong to onboarding Step 0, in its own flow.

`isolation` (extractor write-isolation, U0 spike (c)) is recorded, not probed here: `verified` only where the OS-level deny was actually exercised on this host (`engine/docs/write-isolation-config.md`); doc-derived ⇒ `unverified`.

## Step 3 — Write the row (the only writer)

- Rows live in a fenced `runtime:` YAML block in `config.md`'s **body**, keyed by host — **not** frontmatter (the dependency-free frontmatter parser is flat-only). Shape: `engine/templates/config.md` → "Runtime capabilities". Include `outbound_gate:` explicitly, mirroring the hooks state — a degraded gate must be observable in the row, not implied.
- **Fail-closed defaults applied on write:** `hooks` ≠ `verified` ⇒ keep the read-only OAuth floor on outward connectors + state a session notice that the structural gate is degraded. `isolation` ≠ `verified` ⇒ `person_enrichment_default: false` (and `person_enrichment.enabled: false` unless the principal explicitly opts in).
- **Append/update your OWN host's row only — never overwrite another host's.** The same instance folder gets opened from multiple hosts; runtime is a session property, not an instance property. `cos-system-maintenance` re-probes `unverified` capabilities weekly; the scheduled cold path never fabricates rows.
- **`schema:` marker:** on a NEW instance the template ships `schema: 1` in `config.md` frontmatter (onboarding writes it). On an EXISTING instance, preflight adds/updates its `runtime:` row and touches nothing else — it never adds or bumps `schema:` (migration owns that).

## Per-session selection (mirrored in `engine/INSTRUCTIONS.md` §3)

- Every session selects the row matching the **live** detect-or-ask host. Never apply another runtime's wiring.
- Missing row or host mismatch in an **interactive** session ⇒ run this skill.
- **Non-interactive** (scheduled) session ⇒ fail closed: read-only floor, enrichment off, **no probes, no config writes**; append a "preflight needed for host `<X>`" line to `log/runs/` for the next interactive session to surface.
- Duplicate rows for one host ⇒ select the newest `last_verified`; queue cleanup as a validation finding — never silently delete.

## Verification
- A Cowork session with CLI-style artifacts on disk is not recorded as `claude-code` (detect-or-ask, never disk inference).
- Every capability in the written row is one of `verified | unverified | unavailable` with a `last_verified` date; `outbound_gate` matches `hooks`.
- On Cowork the row reads `hooks: unavailable` (citation, no outward canary), `scheduling` carries the ~7-day/app-open expiry note, and `person_enrichment_default: false` unless isolation was OS-verified.
- A second host's existing row is untouched after a run; an existing instance's `schema:` is untouched.
- No content item (email subject, event body) is read during the connector inventory.

## Output contract
| Artifact | Template | Path | Required frontmatter |
|---|---|---|---|
| runtime row (config update) | `engine/templates/config.md` | `config.md` (body `runtime:` block; `schema: 1` on NEW instances only) | `type`, `date` |
| capture footer | `engine/templates/capture-footer.md` | `log/runs/<date>-<run>.md` | (appended block) |

## Capture footer
End with `engine/templates/capture-footer.md`.
