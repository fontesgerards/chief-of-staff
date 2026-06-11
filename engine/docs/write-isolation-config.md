# Write-isolation config — making the extractor structurally read-only

> Operationalizes U6 / KTD-5. The extractor (`engine/skills/cos-extract-from-sources/SKILL.md`) must be **unable** to write `instance/memory/` — a denied capability, not an agent choice (an injection can override an instruction; it cannot override a denied capability). Researched 2026-06-04; see `U0-capability-spike.md` (c).
>
> **Key principle — isolate per run, not globally.** A global deny on `instance/memory/` would also block the legitimate cold-path consolidator, which *must* write memory. So the **extractor runs in a restricted profile/session**; the cold path and other skills run normally.

## Claude Code / Cowork

Run the extractor with a **dedicated restricted settings file** (don't put these denies in the project-wide settings, or you'll block the cold path). Three layers, defense-in-depth:

`extractor.settings.json` (pass via `--settings` when invoking the extraction run, or use a separate session):

```json
{
  "permissions": {
    "deny": [
      "Write(//ABSPATH/instance/memory/**)",
      "Edit(//ABSPATH/instance/memory/**)"
    ],
    "allow": [
      "Write(//ABSPATH/instance/memory/sources/**)",
      "Write(//ABSPATH/instance/log/runs/**)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "denyWrite": ["//ABSPATH/instance/memory"],
      "allowWrite": ["//ABSPATH/instance/memory/sources", "//ABSPATH/instance/log/runs"]
    }
  }
}
```

- `permissions.deny` blocks the built-in `Write`/`Edit` tools **before execution** (unbypassable, precedes `bypassPermissions`).
- `sandbox.filesystem.denyWrite` adds **OS-level** enforcement (Seatbelt on macOS, bubblewrap on Linux) that also covers `Bash` and any subprocess — so even a `bash`-driven write fails with an OS error. macOS/Linux/WSL2 only.
- Optional third layer — a `PreToolUse` hook that `exit 2`s on any `Write`/`Edit` whose path is under `instance/memory/` (custom logic, also unbypassable vs the model).
- Note the **allow** carve-outs: the extractor *may* write `memory/sources/` summaries + `log/runs/` staging, but nothing else under `memory/`.

**Cowork caveat:** confirm Cowork honors settings.json `permissions`/`sandbox` the same as the CLI (likely, but undocumented as of 2026-06). If it does **not**, run the extraction step itself via the Claude Code CLI or Codex sandbox (both enforce it), and let Cowork drive the rest. *Update 2026-06-11:* Cowork does **NOT** fire settings.json hooks (anthropics/claude-code#63360) — apply the same skepticism to `permissions`/`sandbox` until the preflight `runtime:` row verifies them per-host; the extraction-step fallback above stands.

## Codex

Use the **permissions-profile system** (not the older `sandbox_mode`). In `config.toml`:

```toml
default_permissions = "cos-default"          # normal runs (cold path can write memory)

# Restricted profile used ONLY for the extractor run:
[permissions.extractor.workspace_roots]
"." = true

[permissions.extractor.filesystem.":workspace_roots"]
"."              = "write"     # workspace generally writable...
"instance/memory" = "read"     # ...but memory/ is read-only → writes = EPERM
"instance/memory/sources" = "write"   # except staging summaries
"instance/log/runs"       = "write"   # and run staging

[permissions.extractor.network]
enabled = false
```

Invoke the extraction run with `codex --permissions-profile extractor …`. Precedence is `deny > write > read`; `"read"` on `instance/memory` blocks writes at the OS level (SBPL deny / read-only bind mount), and Codex **fails closed** — it refuses to run if it can't enforce the policy. Alternative: scope the extractor's cwd to a staging dir (`--cd …`) so `instance/memory` is entirely outside its workspace.

## Web sources — the two-step (research)

The restricted extractor profile has **network off** (`network.enabled = false` / `[permissions.extractor.network] enabled = false`), so it cannot fetch the web. `cos-research` must therefore split fetching from extraction so untrusted external content is never reasoned-over with memory-write access:

1. **Fetch-to-file (network-on, no memory write beyond `sources/`).** A retrieval step writes raw pages to `instance/memory/sources/web/` **without loading the body into a memory-capable acting context** — pipe bytes to disk (`curl -fsSL <url> -o instance/memory/sources/web/<slug>.html`, or a WebFetch whose output is written straight to file), don't reason over the content. This step needs network but **no** write to `instance/memory/{core,semantic,procedural}/`; restrict it the same way (memory read-only except `sources/`), network on.
2. **Isolated extraction (restricted, network-off).** The standard extractor profile above reads `instance/memory/sources/web/` and stages tuples — identical to any other `source_kind`.

If a runtime cannot fetch-without-loading (no file-piping tool, body always enters context), research falls back to **datamark-discipline-only** for that fetch and must say so — it's weaker than OS isolation, and the append-only + stage-changes rule is then the only guard.

## Verification (the U6 test, made real)

From inside a restricted extractor run, attempt `echo x > instance/memory/test.md`:
- **Expected:** a runtime/OS-level error (permission denied / EPERM / harness block), **not** the agent saying "I shouldn't do that."
- Writing `instance/memory/sources/probe.md` and `instance/log/runs/probe.md` **succeeds** (the carve-outs work).
- The same write from the *normal* (cold-path) profile **succeeds** — proving isolation is per-run, not global.
- **Web two-step:** the network-on fetch step writes only under `instance/memory/sources/web/`; the network-off extractor stages from those files — neither step writes canonical `instance/memory/`.

## Outward enforcement — the gate as layer 2 (propose-never-act made structural)

> The sections above isolate **inward** writes (memory). This one isolates **outward** actions (`INSTRUCTIONS.md` §1) — send/post/schedule/mutate-external. Same creed (`write-back.md` §8.2: "you can't scan your way out"): the enforced invariant is *no outward action without a payload-matched approved proposal*, applied by the strongest mechanism each surface offers. **The principle is portable; the PreToolUse hook is not.**

Three layers, and you want all three — the gate alone is necessary, not sufficient (it watches MCP tool names, not `Bash` egress like `curl`/`osascript`):

| Layer | Mechanism | CLI | Cowork | Codex |
|---|---|---|---|---|
| **1. Read-only OAuth scopes** | provider-enforced (the agent never holds the write capability) | ✅ | ✅ **primary posture** | ✅ |
| **2. Per-proposal payload-bound gate** | `PreToolUse` hook (`engine/eval/hooks/outbound_gate.py`) | ✅ full | ❌ **does not fire** (2026-06-11, anthropics/claude-code#63360) | ❌ no hook → approval-policy |
| **3. Bash-egress deny** | OS sandbox network/exec (Seatbelt/bubblewrap) | ✅ | ⚠️ unverified | ✅ `network.enabled=false` |

### Claude Code (the reference implementation)
Wire the gate via `.claude/settings.json` (the `PreToolUse` block in `engine/eval/hooks/settings.example.json`): matcher `mcp__.*` invokes `outbound_gate.py`, which classifies outward-vs-read from `outbound_gate.config.json`, reads the autonomy dial from `instance/config.md`, and denies (`exit 2`) anything that isn't a payload-matched approved proposal at a permissive dial. **Fail-closed** — unreadable config/queue/dial denies. `cos-onboarding` writes this by default (Step 7).

### Cowork
Connectors are wired from the plugin's Connectors tab (bundled) or Customize → Connectors (built-ins), and the read-only/write choice is made at the **OAuth consent screen** — so **layer 1 carries the weight**: connect read-only and the agent *cannot* mutate, hook or no hook. *Update 2026-06-11:* the gate hook does **NOT** fire on Cowork — settings.json hooks aren't honored there (anthropics/claude-code#63360); `cos-preflight` records `outbound_gate: unavailable` in the host's `runtime:` row. Layer 1 is therefore the **enforcement floor**, not defense-in-depth: keep outward connectors read-only on Cowork; the principal executes approved sends.

### Codex
No pre-tool hook, so automated payload-bound matching isn't reachable the same way. Enforce with a **restricted acting permissions-profile** (parallels the extractor profile above) that either omits the mutating MCP server or uses Codex's **approval policy** for per-tool human approval; Codex **fails closed** (refuses to run if it can't enforce). What you get is *read-only scopes + human approval* — a **coarser** gate than the CLI's (it confirms a human approved the call, not that the payload equals the approved one).

> **Verify-at-build (KTD-7):** does Codex expose any pre-tool-call **script** hook? If yes, port `outbound_gate.py` to it for true payload-bound matching. If no, Codex enforcement stays read-only-scopes + approval-policy, and that limit must be stated honestly — **payload-bound matching is a Claude Code capability, not a cross-platform guarantee.**

### Verification (outward gate)
With a write scope granted on Claude Code, a direct `create_event` call with **no matching approved proposal** must fail with a **hook block (`exit 2`)**, not the agent saying "I should propose instead." A call whose canonicalized args match an `approved` proposal's `args_digest` is allowed; editing the proposal breaks the match; an irreversible action cannot execute twice (token consumed); unreadable config/queue denies. Executable coverage: `python3 -m pytest engine/eval` (`hooks/test_outbound_gate.py`, `lib/test_outbound.py`); contract map in `engine/eval/scenarios/02-outbound-gate/README.md`.
