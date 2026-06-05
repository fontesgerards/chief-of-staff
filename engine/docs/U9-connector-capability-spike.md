# U9 — Connector Capability Spike (GATE for Phase B)

> Run this **before** relying on `methods/connectors.md` and the onboarding Step 0 connector flow. It confirms the three capabilities Phase B assumes but the original U0 spike never tested. Throwaway investigation — output is the results table at the bottom, referenced by `methods/connectors.md` and `cos-onboarding/SKILL.md`.
>
> **Why it gates:** the connector design was built from a single web-research pass that gave *conflicting* endpoint URLs — so the commands, schemas, and runtime behaviors it hardcodes must be verified against the live tools, not trusted. A wrong CLI verb or a config that doesn't take effect in-session breaks the whole flow, and verify-by-probe won't catch it.

## Run per surface: Claude Code CLI · Codex · Cursor · Cowork

### (a) Runtime self-detection — can a skill know its host?
- **Probe:** from inside a running skill, look for a reliable host signal (env var, available CLI, tool namespace). Record what — if anything — uniquely identifies each runtime.
- **Critical test:** confirm a **Cowork** session that shares a Claude-Code-style filesystem (`.mcp.json` present, `claude` on PATH) is **not** mis-detected as Claude Code CLI — file presence ≠ active host.
- **Pass:** a reliable signal exists per surface. **Fallback (expected for ambiguous cases):** the skill **asks the principal** which runtime they're in (KTD-5). Record which surfaces need the ask.

### (b) Config-write-takes-effect — and when?
- **Probe:** write the runtime's MCP config from inside a session, then try to use the server. Record whether it becomes usable **in-session** or only **next-invocation / after a reload**.
  - Expected (verify, don't trust): Claude Code = in-session (no restart); Codex = next-invocation; Cursor = after `MCP: Reload`. 
- **Pass:** config-write works; the load-order is recorded so verify-by-probe runs on the right turn (KTD-4). This is the capability U0(b) never tested — U0(b) only confirmed *reading through an already-wired connector*.

### (c) Command / schema reality (KTD-7)
- **Probe:** run the actual help/inspection for every command and schema the method will hardcode:
  - `claude mcp add --help`, `claude mcp list --help`
  - `codex mcp --help` (confirm `add` / `login` / `list`), inspect a `[mcp_servers.<id>]` stanza
  - Cursor `.cursor/mcp.json` shape + the `auth` block fields (does it really hold CLIENT_SECRET? → KTD-10 keychain routing)
- **Pass:** each verb/schema exists at the installed version. Any drift → correct `methods/connectors.md` before it ships a command that errors.

## Results (fill in)

| Surface | (a) detect signal / ask? | (b) config-write + load timing | (c) commands/schema verified? |
|---|---|---|---|
| Claude Code CLI | | | |
| Codex | | | |
| Cursor | | | |
| Cowork | (UI-only — expect ask) | (n/a — no programmatic config) | (n/a) |

**Feeds:** `methods/connectors.md` (mechanisms + the per-surface Quick-reference), `cos-onboarding/SKILL.md` Step 0 (detect-or-ask + load-order verify), and U8's `config.md` connector status schema. A "no" on (a) for a surface locks the ask-the-user fallback there; a surprise on (b)/(c) corrects the method before it's authored as fact.
