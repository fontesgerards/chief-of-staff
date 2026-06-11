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
├─ setup.sh · INSTALL.md   ← all install paths (INSTALL.md); setup.sh serves the clone path only
└─ PUBLISH.md
```

## One-time: publish

1. The GitHub URL is already set to `fontesgerards/chief-of-staff` in all three manifests + `marketplace.json`.
2. Push this repo to the **public** repo `fontesgerards/chief-of-staff`.
3. (Optional) Tag a release matching the version in the manifests (`engine/.claude-plugin/plugin.json` — currently `0.7.0`): `git tag v0.7.0 && git push --tags`.

## How a user installs (Claude Code)

```text
/plugin marketplace add fontesgerards/chief-of-staff
/plugin install chief-of-staff@chief-of-staff
```

Then:

```text
/cos-onboarding
```

`/cos-onboarding` **confirms where the instance folder lives** (Step 0a — default `~/Documents/chief-of-staff`, else `~/chief-of-staff`; **never silently the current working directory**), creates `instance/` there, and writes a `CLAUDE.md` + `AGENTS.md` so behavior auto-loads every session. The plugin (engine) is global; the instance is theirs and local.

## How a user installs (Cowork)

No terminal: **Customize → Plugins → Browse plugins** → install **chief-of-staff** from the `fontesgerards/chief-of-staff` marketplace. Skills surface as slash commands; the user opens the folder for their brain and runs `/cos-onboarding`. The preflight records Cowork's real capabilities (schedules expire ~7 days / app-open only; settings.json hooks don't fire — anthropics/claude-code#63360 — so connectors stay read-only at the OAuth screen). Plugin-tab connectors (Granola/Zoom/Fathom/Fireflies/Slack) come from the shipped `engine/.mcp.json`; Gmail/Calendar/Drive are Anthropic built-ins via **Customize → Connectors**. After updates that change `.mcp.json`, the user must re-sync the plugin from the marketplace. Full steps: `INSTALL.md` Path 1.

## How a user installs (Cursor)

Cursor reads `engine/.cursor-plugin/plugin.json` and auto-discovers the `engine/skills/<name>/SKILL.md` skills (Cursor's plugin system has been native since v2.5). The repo ships a `.cursor-plugin/marketplace.json` (mirroring the Claude one). Add the marketplace and install per Cursor's plugin docs, then `/cos-onboarding`. Skills are invocable as `/cos-<name>` in Agent chat.

## How a user installs (Codex)

Codex consumes the same `engine/` via its `.codex-plugin/plugin.json` (a real, native Codex manifest — `interface` block + `agents/openai.yaml` sidecar are valid). Skills install natively. We ship **no** `.codex-plugin/marketplace.json` because Codex's marketplace flow is less settled than Claude's — follow the current Codex plugin docs to add the repo (`codex plugin marketplace add fontesgerards/chief-of-staff`, per docs), or drop skills in directly: `cp -r engine/skills/* ~/.agents/skills/`. Then `$cos-onboarding`. (No subagent layer to convert — we ship only skills, so install is clean.)

## Alternative: no plugin, just clone

For users who'd rather not install a plugin (or want to hack on it): `git clone`, `./setup.sh`, open the folder, `/cos-onboarding`. See `INSTALL.md`.

## Naming

Every skill is prefixed **`cos-`** (chief of staff), so commands are namespaced and collision-safe across other installed plugins/built-ins: `/cos-onboarding`, `/cos-meeting-prep`, `/cos-loop-closing`, … (Claude) and `$cos-…` (Codex). This mirrors Compound Engineering's `ce-` convention. The plugin itself is named `chief-of-staff`; only the skills carry the `cos-` prefix.

## Validation status

| Item | As of | Status |
|---|---|---|
| `.claude-plugin/marketplace.json` | 2026-06-05 | Validated against live Claude docs + the compound-engineering marketplace (which ships the same `metadata` + `source: <path>` shape). |
| `engine/.claude-plugin/plugin.json` | 2026-06-05 | Validated — valid as-is; skills auto-discovered from `skills/`. |
| `engine/.codex-plugin/plugin.json` | 2026-06-05 | Matches the compound-engineering Codex manifest field-for-field (incl. `skills: ./skills/` + `interface`). Native Codex format. |
| `engine/.cursor-plugin/plugin.json` | 2026-06-05 | Corrected to match the compound-engineering Cursor manifest: **no `skills` field** (auto-discovered), added `displayName`. |
| `.cursor-plugin/marketplace.json` | 2026-06-05 | Added (mirrors CE's `pluginRoot` + bare `source`). |
| Cowork install path (Customize → Plugins → Browse) | 2026-06-11 | **Documented; smoke-test pending.** Capability facts (hooks don't fire, ~7-day schedule expiry) sourced from support docs + anthropics/claude-code#63360; one real Cowork install + onboarding run still owed. |

**Smoke-tests still owed:** (1) the Cowork install path end-to-end — one real Customize → Plugins install + `/cos-onboarding` run; (2) the Cursor marketplace `source`/`pluginRoot` resolution to `engine/` (CE uses `plugins/<name>`; we use a single `engine/`). The Claude Code path is the most thoroughly verified.
