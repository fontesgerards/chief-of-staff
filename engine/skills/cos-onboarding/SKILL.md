---
name: cos-onboarding
description: Set up your AI Chief of Staff — observes your email/calendar to draft a profile, captures your writing voice, seeds your private memory, and hands you a how-to. Run this first. Re-run to re-seed.
disable-model-invocation: true
kind: installer
run: once (or to re-seed)
---

# cos-onboarding — the installer (observe, don't make me teach you)

> One conversation that stands up a working `instance/` from the engine's `templates/` and hands the principal a `GETTING-STARTED.md`. For the future product, this **is** the activation funnel — each new person just talks to it.
>
> **Where the instance goes:** the principal's brain (`instance/`) lives in a dedicated folder they choose at the start (**Step 0a**) — defaulting to a detected home subfolder (`~/Documents/chief-of-staff`, else `~/chief-of-staff`), **never silently in the current working directory and never at the filesystem root.** The engine (templates, methods, this skill) is resolved from the plugin package (`${CLAUDE_PLUGIN_ROOT}`); `instance/` is resolved from the chosen instance folder (engine `AGENTS.md` → "Two roots"). If an `instance/` already exists there, confirm before re-seeding.
>
> **Prerequisites:** run the U0 spike (engine `docs/U0-capability-spike.md`, extractor isolation) and the U9 connector spike (`docs/U9-connector-capability-spike.md`, runtime detection / config-write / commands) first — they tell this skill what's automatable on the host.

---

## Interaction Protocol (read before running any step)

These five rules govern every step. They are the difference between a runbook and an improvised chat.

1. **One question at a time.** Never dump a list. Ask, **wait for the answer**, then ask the next. A "25-question wall" is forbidden (it's exactly what observe-first exists to avoid).
   - **Use the runtime's structured-question tool when it has one.** On Claude Code, prefer the **`AskUserQuestion`** tool for any question with a small set of likely answers (confirm-by-exception choices, autonomy/boundary picks, connector selection) — it gives the principal tappable options with an "Other" escape hatch and reads far better than free-text in a terminal. Codex/Cursor equivalents (or the harness's native choice/elicitation prompt): use them the same way. Where no such tool exists, fall back to plain one-at-a-time prose. The tool is for *choices*; open-ended "what's broken now?" gaps stay conversational.
2. **Observe → draft → confirm → fill.** The default order for every observation-backed step:
   - **Observe** from connectors/sources (read-only extractor).
   - **Draft** the artifact from what you observed.
   - **Confirm by exception** — *show what you inferred and ask "what's off?"* This is the opening move, not a blank interrogation.
   - **Fill gaps** — ask **only** the bank questions observation couldn't answer (one at a time).
3. **Low-observation fallback (degraded mode).** When connectors aren't wired (Step 0 declined/blocked) and there's little to observe, lead with the relevant question bank — but ask only the **must-ask** items, say you're asking because you can't observe yet, and **re-observe + re-draft after connectors land later**. This is a *designed* mode, still one-at-a-time — not the 25-question wall.
4. **Hard approval gate before any `core/` write.** `core/` (identity, operating-context, voice, autonomy, current-priorities) is Tier-2-protected everywhere else; onboarding writes it fresh, so **show the drafted file and get an explicit "yes" before writing it.** No silent `core/` writes.
5. **Everything seeded carries `origin: imported`.** Seeded facts must not auto-trust into `core`/`procedural` (the tier gate). Observation is `observed`; principal-confirmed facts become `confirmed`.

**Per-step shape (uniform):** *Observe → Draft (→ template) → Confirm/fill (→ question bank) → Gate (if `core/`) → Write (`origin: imported`).*

---

## The steps

### Step 0a — Confirm where the brain lives (FIRST action, before anything else)

> Personal data must never be seeded into a random/synced folder. **Do not assume the current working directory.** Most CLI sessions launch from somewhere incidental (a code repo, a notes vault, home) — seeding `instance/` there is almost always wrong.

1. **Detect the best home subfolder, then propose it.** Resolve the principal's home (`~`) and probe for a sensible, non-synced parent — prefer `~/Documents` if it exists and isn't cloud-synced, else fall back to `~` (home root). **Never** propose the filesystem root, a system dir, or the current working directory. Then confirm: *"Your Chief of Staff's private brain will live at `~/Documents/chief-of-staff/instance` — sound good, or pick another folder?"* (substitute the detected parent). Accept any absolute path the principal gives.
2. **Warn if the chosen parent looks risky:** inside a cloud-synced folder (iCloud/Dropbox/OneDrive — note `~/Documents` is iCloud-synced on many Macs, so probe before preferring it), inside another git repo, the filesystem root, a system directory, or the raw cwd. Personal brain data syncing to a cloud notes folder is a privacy footgun — recommend a dedicated, non-synced `chief-of-staff` folder instead.
3. Create the folder if needed and **anchor all subsequent `instance/…` paths to it for the rest of the run.** Record the chosen path so the entry files (Step 8) and re-runs resolve to the same place.

### Step 0 — Connectors (step-zero, after location is confirmed)

> Attempt connector setup **before** discovery so observation has data. If it's declined or can't complete, proceed in **degraded mode** (Protocol §3) and re-observe later. Full mechanics: engine `methods/connectors.md`.

1. **Detect-or-ask the runtime.** Use a reliable signal if the host exposes one (per the U9 spike); otherwise **ask** the principal which runtime they're in (Claude Code / Cowork / Codex / Cursor). Never guess from on-disk config presence.
2. **Inventory what's already connected — observe before you ask (the connector confirm-move).** Before proposing any setup, **classify-probe every connector you can reach** (tiny read: 3 calendar events / 3 email subjects / list recent recordings) to see what's *already configured + authorized* in this runtime. Then **show the principal the live inventory** — e.g. *"You've already got Gmail, Calendar, and Granola connected. I don't see Slack or Zoom yet — want to add either, or anything else?"* — and ask **what else** to wire. This is the connectors version of observe→confirm→fill: never make the principal re-set-up what's already there, and never present a blank "connect these 8 things" wall. Skip already-verified connectors in the per-connector setup below.
3. **For each *remaining* connector the principal wants:**
   - **Recordings + messaging** are **bundled** in the plugin's Connectors tab: **Granola · Zoom · Fathom · Fireflies · Slack** → click Connect → OAuth.
   - **Email / Calendar / Drive (Google)** are **Anthropic built-in connectors** — guide the user to **Customize → Connectors** (or claude.com/connectors) → Connect Gmail/Calendar (zero setup). **Do NOT** expect these in the plugin tab; the Google MCP URLs can't be bundled (no DCR — see `methods/connectors.md`). On **Claude Code CLI**, built-in Google may be stub-only → use **degraded mode** (interview + file-drop into `sources/`) and connect Google from Cowork/Desktop.
   - **Microsoft** (Outlook/Teams): built-in **Microsoft 365** connector from Customize → Connectors (also not bundleable).
   
   Then, for each connector being wired:
   - **Re-probe if stale** — the Step 0.2 inventory already classified each connector (a thrown probe is **never** a hard error: treat as "not yet connected, proceed"). Only re-probe here if the inventory is stale or the principal just took action.
   - **Configure** (automatable surfaces — Claude Code CLI / Codex / Cursor): write the MCP config per `methods/connectors.md`. **Secrets go to the keychain/env-ref, never into the config file; workspace-local configs (`.mcp.json` / `.cursor/mcp.json`) are gitignored + sync-excluded — guide the principal to exclude manually where the runtime can't; Codex's user-home config needs neither; request the least-privilege (read-only) scope and show it to the principal before the click.** On **Cowork**, Gmail/Calendar/Drive are **bundled in the chief-of-staff plugin** (`engine/.mcp.json`) — guide the user to the **plugin's Connectors tab → Connect → OAuth** (prefer read-only on the consent screen; tell them what they're granting). Nothing to configure or store — it's declared in the shipped `.mcp.json`.
   - **Guide the one OAuth click** (showing the scope). This is the only unavoidable user action.
   - **Verify load-order-aware** — on Codex (next-invocation) / Cursor (reload) the just-wired connector is live **next turn**; a same-turn probe miss is **not** failure. On Claude Code, verify in-session.
   - **Record status** in `config.md` (`connected | pending | verified | blocked`, surface, last-verified). If OAuth is declined or admin-blocked: status `blocked`, continue in degraded mode (no retry loop).
4. **Third-party egress is off the default path.** Composio / any non-first-party hosted server is offered **only** on explicit request, with a "your data leaves your machine" consent shown at the click (KTD-6, `methods/connectors.md` trust tiering).

**Connector-step verification:** at most one shown-scope OAuth click per connector; no secret in any written file; correct per-surface + load-order behavior; declined/blocked yields degraded mode, not a loop.

### Step 1 — Identity → `core/identity.md`  *(gate)*
- **Observe:** role/company/mandate from email signature, calendar, docs.
- **Draft** `core/identity.md` from the template.
- **Confirm/fill:** show it, ask "what's off?"; then the **identity bank** gaps (`references/discovery-questions.md`) — esp. *what's broken now* and *what you've tried that failed* (rarely observable).
- **Gate → Write** (`origin: imported`/`confirmed`).

### Step 2 — Operating context → `core/operating-context.md`  *(gate)*
- **Observe** the world they operate in (org, market, key relationships) and seed `semantic/` people/accounts from recent activity.
- **Draft → Confirm/fill** (how-you-work bank) **→ Gate → Write.** Seed `semantic/` entities `origin: imported`.

### Step 3 — Boundaries → `core/autonomy.md`  *(gate)*
- Mostly **not observable** — ask the boundaries bank (one at a time): *what should I NEVER do*, *what would make you stop using me*. These tune the autonomy dial.
- **Draft → show → Gate → Write** `core/autonomy.md` (autonomy stays propose-only; record the "always ask before…" rules).

### Step 4 — Voice → `core/voice.md` + `procedural/drafting.md`  *(gate)*
- **Observe:** pull 3–5 real sent messages across contexts.
- **Draft** voice characteristics, register, sign-offs, quirks, **"what my voice is NOT,"** banned words (`references/voice-questions.md` fills gaps).
- **Confirm with a concrete sample — don't make them judge an abstract profile.** Before the gate, **compose one short email in the captured voice and show it inline in the conversation** so the principal can react to *output*, not adjectives. Base it on a **real recent/unread inbox thread** when one is available (read-only — use what the connectors already surfaced to ground the reply); if nothing suitable is in the inbox or email isn't connected, generate a plausible email from the operating-context (e.g. a reply to a recurring counterpart, or a typical status note). Ask *"does this sound like you? what's off?"* and fold the corrections back into the voice draft before writing. **Render the sample as text in the chat only — do NOT call any email/draft tool (no `create_draft`, no compose, no save-to-client) and never queue or send it. It exists purely to calibrate `core/voice.md`.**
- **Gate → Write:** `core/voice.md` within its `budget_chars`; annotated samples + the long banned-list overflow to `procedural/drafting.md` (unbounded).

### Step 5 — Glossary → `semantic/` glossary
- **Observe** recurring acronyms / jargon / nicknames from sources (don't ask cold).
- **Confirm** the list → write `semantic/glossary.md` (template `templates/glossary.md`), `origin: imported`.

### Step 6 — Seed the five-type memory
- Instantiate `core/` (gated above), `semantic/`, `episodic/` (recent), `procedural/` (template), `sources/` (with retention), plus `state/`, `queue/`, `log/`, optional `index/` from `templates/`. **All seeded facts `origin: imported`.** A dense, correct seed bootstraps usefulness and hardens against later poisoning.

### Step 7 — Config & schedule → `config.md`
- Autonomy = propose-only; fill `connectors:` (names + status from Step 0), `schedules:` (cadence per skill), `queue:` lifecycle, `write_back:` tuning. **No secrets** (keychain/env-ref only). Initialize the `instance/` backup repo (`.backup-instructions.md`).

### Step 8 — Entry files → working-folder `CLAUDE.md` + `AGENTS.md`
- Write thin entry files (template `templates/entry-CLAUDE.md`) so behavior auto-loads every session: identity one-liner + **safety floor inlined** + pointer to the engine's `INSTRUCTIONS.md`. Inlining the floor keeps the folder safe even if the plugin path can't resolve.

### Step 9 — Graduation doc → working-folder `GETTING-STARTED.md`
- Write the human-facing how-to (template `templates/getting-started.md`) in the principal's **own voice** (reads `core/voice.md`): how it works, what's connected (reflect live `config.md` status — pending/blocked shown honestly, never as configured), the `/cos-*` commands with example prompts, the correction loop, the weekly rhythm, honest limitations. **Generatable from interview-only state** so an abandoned-at-OAuth run still leaves a working assistant + how-to (the activation backstop).

---

## Output
A populated, scheduled, working `instance/` in the current folder + `CLAUDE.md`/`AGENTS.md` entry files + a `GETTING-STARTED.md`. Opening this folder in the runtime + this run = a functioning system.

## Verification (test scenarios)
- **Pacing:** questions asked one at a time, each waiting — never a dumped list.
- **Confirm move:** before asking, inferred facts are shown with "what's off?" — not a blank interrogation.
- **Gate:** no `core/*.md` is written before the principal approves the shown draft.
- **Degraded mode:** with no connectors, onboarding still completes via must-ask banks (says it's asking because it can't observe) and re-observes after connectors land — not a 25-question wall.
- **Origin:** every seeded fact is `origin: imported` (grep).
- **Connectors:** see Step 0 verification (one shown-scope click, no secret in any file, surface/load-order correct, degraded on decline). Inventory shown first — already-connected connectors are surfaced and *not* re-requested before asking what else to wire.
- **Location:** Step 0a proposes a detected home subfolder (never `/`, a system dir, or raw cwd); cloud-sync of the chosen parent is probed and warned.
- **Structured questions:** on a runtime with a choice/elicitation tool (e.g. Claude Code `AskUserQuestion`), choice-style questions use it rather than free-text prose.
- **Voice:** a sample email (grounded on a real inbox thread when available, else generated from context) is shown **inline in the chat** for "sound like you?" calibration — no email/draft tool is called, nothing queued or sent; `core/voice.md` within budget; overflow in `procedural/drafting.md`.
- **Graduation:** `GETTING-STARTED.md` lands in the user's voice, reflects live status, lists `/cos-*` commands.

> **Deferred to product track:** multi-tenant regeneration + data-isolation. Not a v1-of-one concern.

## Capture footer
End with `engine/templates/capture-footer.md`.
