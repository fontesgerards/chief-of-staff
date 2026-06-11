<!-- Template for GETTING-STARTED.md — written by onboarding Step 9 into the principal's WORKING FOLDER
     (next to instance/). This is the HUMAN-facing how-to (distinct from the machine-facing CLAUDE.md/
     AGENTS.md entry files). Write it in the PRINCIPAL'S OWN VOICE (read core/voice.md).
     It must be generatable from interview-only / no-connector state — an abandoned-at-OAuth run still
     leaves a working assistant + this guide (the activation backstop). Reflect LIVE config.md status:
     show pending/blocked connectors honestly, never as configured. -->

# Your AI Chief of Staff — getting started

**The 30-second version.** {{One or two sentences, in your voice: what this is and what it does for you.}}

## What's set up

- **Memory:** seeded — {{which core/ files, roughly how many people/accounts}}.
- **Connectors:** {{per connector: ✅ connected & verified · ⏳ pending your OAuth click · ⛔ blocked (admin) — with the one action to finish each. NEVER list a pending connector as connected.}}
  - Want to connect more later? Meeting recordings and Slack live in the **chief-of-staff plugin's Connectors tab**; Gmail / Calendar / Drive connect under **Customize → Connectors** (they're Claude built-ins, not plugin entries). The full map is in the engine's `methods/connectors.md`.
- **Voice:** captured from your real messages.
- **Runs on its own:** {{scheduled skills + cadence from config.md schedules, by real status — ✅ live (actually firing — and if this host's runtime row says the registration expires, say so in the status itself, e.g. "live (expires ~7 days after registration — I'll prompt you to re-arm)") · 🔧 needs one setup step (status: manual — name the click, e.g. "add it in the Cursor dashboard") · 📝 recorded only, not yet running (status: intent-only). NEVER describe a manual/intent-only schedule as already running, and never show an expiring schedule as plain "live" without its expiry caveat.}}.

## How to use it day-to-day

Type these (Claude: `/`, Codex: `$`):

| Command | What it does | Try |
|---|---|---|
| `/cos-meeting-prep` | preps you for upcoming meetings | "prep me for tomorrow" |
| `/cos-meeting-follow-up` | captures outcomes + drafts follow-ups | run it after a call |
| `/cos-loop-closing` | surfaces stalled / ownerless items | weekly |
| `/cos-coaching` | strengths-based weekly nudge | Friday |
| `/cos-research` | competitor / market digest | weekly |
| `/cos-goal-setting` | monthly priorities | start of month |

## When it gets something wrong

Just tell it. Corrections are logged and, when they recur, **promoted into how it works** (the weekly consolidation). Over time it makes the same mistake less. You never have to "configure" it — you correct it.

## What it won't do (honest limits)

- **It proposes, you approve.** It never sends an email, posts, or schedules without showing you the exact text first.
- **Connectors need one OAuth click each** — that's the one step nobody can automate away.
- {{any pending/blocked connector + what you'd do to finish it}}.

## Your weekly rhythm

{{In your voice: what happens each day/week automatically, and the one 5-minute review worth doing.}}
