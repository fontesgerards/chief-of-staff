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
- **Pass criterion:** a skill can read these without a human pasting content.
- **Fallback if absent:** file-drop (`instance/memory/sources/{emails,calendar,transcripts}/`) or manual paste. Scope U9's "observe how you work" claim to whatever is real.

### (c) Write-isolation — can a skill be denied write access to `instance/memory/`? **(highest-value probe)**
- **Probe:** run a skill granted a read-only / write-to-`staging`-only scope; have it *attempt* to write `instance/memory/test.md`.
- **Pass criterion:** the write produces a **runtime-level error**, not merely the agent declining. (An agent refusal is not isolation — an injection can override an instruction; it cannot override a denied capability.)
- **Fallback if absent:** run the extractor as a separate session/identity with no memory-write tool. If *neither* is enforceable, **KTD-5 downgrades from "structural" to "defense-in-depth"** — raw-diff review + the provenance tier gate become primary, and U6 + the README say so explicitly.

## Note on portability

Runtime-portability rescues (a) and (b) — a different scheduler or connector is a swap. It does **not** rescue (c): if no available runtime can enforce write-isolation, the structural injection guard has no portable substitute. Treat (c) as the probe that can force a design change.

## Results (fill in)

| Capability | Result | Confirmed mechanism / chosen fallback | Feeds |
|---|---|---|---|
| (a) Scheduling | ☐ pass ☐ fallback | | U8 `config.md` schedules |
| (b) Connectors | ☐ pass ☐ fallback | | U9 ingestion + R4 "observe" claim |
| (c) Write-isolation | ☐ pass ☐ fallback ☐ none | | U6 extractor; KTD-5 framing |

**If (c) = none:** edit `engine/methods/write-back.md` §8.2 and the README to state the injection defense is defense-in-depth, not structural, and elevate raw-diff review + provenance gate to primary.
