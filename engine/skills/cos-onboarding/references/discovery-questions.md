# Discovery question banks (cos-onboarding)

> Pulled by the onboarding runbook (`../SKILL.md`). **These are gap-fillers, not an interview.** Per the Interaction Protocol: observe → draft → confirm → then ask **only** the questions observation couldn't answer, **one at a time**. Each question is tagged:
> - **`[obs]`** — usually answerable from email/calendar/docs; *confirm*, don't ask, when observed.
> - **`[ask]`** — rarely observable; ask if not already volunteered.
> - **`[must]`** — high-value, ask even in a hurry (these are the degraded-mode floor when there are no connectors).

Coverage matches chlokey's discovery depth; framing is ours.

---

## Bank A — Identity → `core/identity.md`
1. `[obs]` What do you do day-to-day? (role, company, the actual work — not the title)
2. `[obs]` Who do you serve / who are your key stakeholders?
3. `[ask][must]` What are you working toward — the goals that matter this quarter and beyond?
4. `[ask]` What does "good" look like for you — how do you know a week went well?
5. `[ask][must]` **What's broken in how you work right now?** (the pain this assistant should attack)
6. `[ask][must]` **What have you tried before that didn't work?** (so we don't rebuild a dead end)

## Bank B — How you work → `core/operating-context.md` + `procedural/`
1. `[ask]` How do you like information presented — bottom-line-first, detail, bullets?
2. `[ask]` When are you most productive? Morning/night, deep-work blocks vs steady-state?
3. `[ask][must]` For complex tasks: do you want me to **ask first**, or **show a draft** and let you react?
4. `[obs]` What tools/systems do you already live in?
5. `[ask]` What's your biggest time sink right now?

## Bank C — Boundaries → `core/autonomy.md`  *(mostly `[ask]` — not observable)*
1. `[ask][must]` **What should I NEVER do without asking you first?** (e.g. anything to investors/board, personnel, external sends)
2. `[ask][must]` **What would make you stop using me?** (the failure modes to design against)
3. `[ask]` Where do you want me more autonomous over time vs always-ask?
4. `[ask]` Any people or topics that are politically/legally sensitive? (also seeds `semantic/relationships/`)

> Bank C answers become `core/autonomy.md` rules ("always ask before …") and `#scope`/`#relationship` standing rules. The autonomy default stays **propose-only**; these tighten it, they don't loosen it.

## Bank D — Priorities → `core/current-priorities.md`
1. `[obs]` From recent activity, here's what looks live right now — what's off? (confirm-by-exception)
2. `[ask][must]` Top 3 things that matter most this month?
3. `[ask]` Anything you've explicitly deprioritized / "not now"?

## Bank E — Research watch list → `procedural/research.md`  *(the "what" for `cos-research`; optional)*
1. `[ask]` What should I track for you each week — **topics / technologies** to watch?
2. `[ask]` Which **companies / competitors** should I keep an eye on?
3. `[ask]` Any **people / influencers / publications** whose moves you want flagged?
4. `[ask]` How do you want the weekly digest — bottom-line-first, sources, length?

> The `cos-research` skill provides the *structure*; this bank provides the *what*. Seed answers into `procedural/research.md` (`origin: imported`). **Optional** — if the principal isn't sure, skip it; research stays dormant until a watch list exists (it won't invent coverage). `[obs]` competitors already in `semantic/` can be offered as a starting set to confirm.

---

## Routing summary (each bank → its write-target)

| Bank | Write-target | Gate? |
|---|---|---|
| A — Identity | `core/identity.md` | yes (core/) |
| B — How you work | `core/operating-context.md` (+ `procedural/` prefs) | yes for core/ |
| C — Boundaries | `core/autonomy.md` (+ `semantic/relationships/`) | yes (core/) |
| D — Priorities | `core/current-priorities.md` | yes (core/) |
| E — Research watch list | `procedural/research.md` | no (procedural, `origin: imported`) |

**Reminder:** every `core/` write goes through the hard approval gate (show draft → explicit yes). Ask `[obs]` items only when observation actually failed; in degraded mode (no connectors) ask the `[must]` items and say you're asking because you can't observe yet.
