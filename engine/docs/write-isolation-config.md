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

**Cowork caveat:** confirm Cowork honors settings.json `permissions`/`sandbox` the same as the CLI (likely, but undocumented as of 2026-06). If it does **not**, run the extraction step itself via the Claude Code CLI or Codex sandbox (both enforce it), and let Cowork drive the rest.

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

## Verification (the U6 test, made real)

From inside a restricted extractor run, attempt `echo x > instance/memory/test.md`:
- **Expected:** a runtime/OS-level error (permission denied / EPERM / harness block), **not** the agent saying "I shouldn't do that."
- Writing `instance/memory/sources/probe.md` and `instance/log/runs/probe.md` **succeeds** (the carve-outs work).
- The same write from the *normal* (cold-path) profile **succeeds** — proving isolation is per-run, not global.
