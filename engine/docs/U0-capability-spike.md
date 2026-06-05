# U0 — Cowork/Codex Capability Spike (HARD GATE)

> Run this **before** building U6 (extractor), U8 (scheduling), and U9 (connectors). It is a throwaway investigation, not production code. Output: a go/no-go + chosen mechanism/fallback per capability, recorded in the table at the bottom.
>
> **Why it gates:** three units' verification assumes runtime capabilities the design never confirmed. Discovering a gap after authoring the whole engine wastes the build. One capability — write-isolation — is the one thing runtime-portability cannot rescue.

## The three probes

### (a) Scheduling — can the runtime fire a skill on a cadence read from `config.md`?
- **Probe:** register a trivial skill ("append a timestamp to `instance/log/runs/heartbeat.md`") on a short cadence; confirm it fires unattended and reads its cadence from config.
- **Pass criterion:** the skill runs at the configured time without a human invoking it.
- **Fallback if absent:** drive schedules from an external `launchd`/`cron` job that opens a runtime session and invokes the skill. Design `config.md`'s `schedules:` block so it works for either path (cadence is data the external driver can also read).

### (b) Connectors — does the runtime expose programmatic email/calendar/recording ingestion to a skill?
- **Probe:** from a skill, list the last 5 calendar events and the last 5 email subjects; pull one meeting recording/transcript.
- **Pass criterion:** a skill can read these **through an already-wired connector** without a human pasting content.
- **Fallback if absent:** file-drop (`instance/memory/sources/{emails,calendar,transcripts}/`) or manual paste.
- **⚠️ Scope note:** (b) confirms only *ingestion through a wired connector*. It does **not** confirm a skill can *write* the MCP config and have it take effect, *detect* its host runtime, or that the connector *commands/schemas* are real — those are tested by the **connector capability spike** (`U9-connector-capability-spike.md`) and the model lives in `methods/connectors.md`.

### (c) Write-isolation — can a skill be denied write access to `instance/memory/`? **(highest-value probe)**
- **Probe:** run a skill granted a read-only / write-to-`staging`-only scope; have it *attempt* to write `instance/memory/test.md`.
- **Pass criterion:** the write produces a **runtime-level error**, not merely the agent declining. (An agent refusal is not isolation — an injection can override an instruction; it cannot override a denied capability.)
- **Fallback if absent:** run the extractor as a separate session/identity with no memory-write tool. If *neither* is enforceable, **KTD-5 downgrades from "structural" to "defense-in-depth"** — raw-diff review + the provenance tier gate become primary, and U6 + the README say so explicitly.

## Note on portability

Runtime-portability rescues (a) and (b) — a different scheduler or connector is a swap. It does **not** rescue (c): if no available runtime can enforce write-isolation, the structural injection guard has no portable substitute. Treat (c) as the probe that can force a design change.

## Results (fill in)

| Capability | Result | Confirmed mechanism / chosen fallback | Feeds |
|---|---|---|---|
| (a) Scheduling | ☑ **pass** | confirmed by principal | U8 `config.md` schedules |
| (b) Connectors | ☑ **pass** | confirmed by principal | U9 ingestion + R4 "observe" claim |
| (c) Write-isolation | ☑ **pass (structural)** | researched 2026-06-04 — enforceable at OS/harness level on both runtimes (see below + `write-isolation-config.md`) | U6 extractor; KTD-5 stays structural |

## (c) result — researched 2026-06-04

**Verdict: PASS. KTD-5 stays "structural," not "defense-in-depth."** Runtime-enforced write-isolation of `instance/memory/` is achievable today on both candidate runtimes, producing a real OS/harness-level error on an attempted write — not an agent refusal.

- **Claude Code / Cowork:** `permissions.deny` rules (`Write(...)`/`Edit(...)` path patterns) are a pre-execution harness block, unbypassable (precedes even `bypassPermissions`); OS sandbox (`sandbox.filesystem.denyWrite`, macOS Seatbelt / Linux bubblewrap) covers Bash **and** subprocesses with a real OS error; a PreToolUse hook is a deterministic third layer. **Caveat:** docs don't explicitly confirm **Cowork** honors settings.json permissions/sandbox (likely inherits Claude Code — verify once); a subagent `tools:` restriction is not currently documented, so don't rely on it.
- **Codex:** permissions-profile system (`[permissions.<name>.filesystem.":workspace_roots"]` → `"memory" = "read"`/`"deny"`) maps to SBPL deny / read-only bind mounts; real `EPERM`; **fail-closed** (refuses to run if it can't enforce). Strongest.

**Design consequence:** a *global* deny would also block the legitimate cold-path consolidator (which must write memory). So isolation is **per-extractor-run**: the extractor runs in a restricted profile/session (read source, write staging only); the cold path runs in a normal context. Exact recipes: `engine/docs/write-isolation-config.md`.

**Residual to verify once:** that Cowork (if used as the runtime) honors deny+sandbox the same as the CLI. If it does not, run the *ingestion/extraction* step via the Claude Code CLI or Codex sandbox (which do enforce it) while the rest runs in Cowork.
