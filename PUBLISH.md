# Publishing the Chief of Staff plugin

This repo is structured as a **single-repo marketplace** (the compound-engineering model):

```
chief-of-staff/                         ← publish THIS repo to GitHub
├─ .claude-plugin/marketplace.json      ← marketplace manifest → points at ./engine
├─ engine/                              ← THE PLUGIN
│  ├─ .claude-plugin/plugin.json        ← Claude manifest
│  ├─ .codex-plugin/plugin.json         ← Codex manifest (+ interface block)
│  ├─ .cursor-plugin/plugin.json        ← Cursor manifest
│  ├─ CLAUDE.md (=@AGENTS.md) · AGENTS.md   ← always-loaded behavior
│  ├─ skills/<name>/SKILL.md             ← the invocable skills
│  └─ methods/ · templates/ · docs/      ← engine internals
├─ instance/        ← gitignored — DEV ONLY; real users generate their own via /cos-onboarding
├─ setup.sh · INSTALL.md   ← the clone-and-symlink path (alternative to the plugin)
└─ PUBLISH.md
```

## One-time: publish

1. The GitHub URL is already set to `fontesgerards/chief-of-staff` in all three manifests + `marketplace.json`.
2. Push this repo to the **public** repo `fontesgerards/chief-of-staff`.
3. (Optional) Tag a release: `git tag v0.1.0 && git push --tags`.

## How a user installs (Claude Code)

```text
/plugin marketplace add fontesgerards/chief-of-staff
/plugin install chief-of-staff@chief-of-staff
```

Then, in the folder they want their brain to live in:

```text
/cos-onboarding
```

`/cos-onboarding` creates `instance/` **in the current working directory** and writes a `CLAUDE.md` + `AGENTS.md` there so behavior auto-loads every session. The plugin (engine) is global; the instance is theirs and local.

## How a user installs (Codex)

Codex consumes the same `engine/` via its `.codex-plugin/plugin.json`. Point Codex at the marketplace/repo per current Codex plugin docs, then run `$cos-onboarding`. (Codex has no subagent layer to convert — we ship only skills, so install is clean.)

## Alternative: no plugin, just clone

For users who'd rather not install a plugin (or want to hack on it): `git clone`, `./setup.sh`, open the folder, `/cos-onboarding`. See `INSTALL.md`.

## Naming

Every skill is prefixed **`cos-`** (chief of staff), so commands are namespaced and collision-safe across other installed plugins/built-ins: `/cos-onboarding`, `/cos-meeting-prep`, `/cos-loop-closing`, … (Claude) and `$cos-…` (Codex). This mirrors Compound Engineering's `ce-` convention. The plugin itself is named `chief-of-staff`; only the skills carry the `cos-` prefix.

> **Verify before publishing:** plugin/marketplace JSON schemas evolve. Cross-check field names against the current Claude Code docs (`/plugin`, plugins-reference, discover-plugins) and the Codex plugin docs. The structures here follow the compound-engineering plugin as of mid-2026.
