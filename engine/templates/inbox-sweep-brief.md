---
type: inbox-sweep-brief
date: YYYY-MM-DD          # filename: state/briefs/inbox-sweep-YYYY-MM-DD.md
covers: YYYY-MM-DD        # the 24h window swept
origin: derived           # observed | confirmed | inferred | imported | derived — assembled from staged summaries; not a standing fact
---

# Inbox sweep — {{date}}

> Written only when the sweep produced something worth saying (drafts queued, questions raised,
> or FYIs worth a glance). An all-ignore day writes no file. If reply drafting was disabled
> (no voice profile), this brief MUST open with:
> "Reply drafting disabled: no voice profile (`core/voice.md`) — run `/cos-onboarding` step 4."

## Drafted for your review
> One line per queued reply proposal — recipient, thread subject, the ask it answers. The drafts
> themselves live in `queue/outbound/`; triage via `/cos-review`.

- {{recipient — subject — the ask, restated}} → `queue/outbound/{{file}}`

## Worth a glance (FYI)
> Threads that need no reply but carry signal — one line each, from the staged summaries.

- {{sender — subject — the one-line so-what}}

## Skipped
> Counts only: {{N}} ignored (automated/newsletters), {{M}} already answered by you, {{K}} left to meeting follow-up.
