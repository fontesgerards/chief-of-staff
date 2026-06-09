---
type: config
created: {{YYYY-MM-DD}}        # onboarding run date
---

# config.md — this instance's settings

> Instantiated by `cos-onboarding` from this template. The single place per-instance behavior is tuned. **Personal — never committed to the engine repo.** Ships with safe defaults: fill `{{…}}` placeholders, leave the rest unless the principal asks to change it. **No secrets ever** (keychain / runtime auth only).

## Autonomy
```yaml
autonomy:
  level: propose-only        # propose-only | act-on-reversible | act-ask-on-risky  (default: propose-only)
  auto_allowed: []           # reversible action types graduated to auto (start empty)
  always_ask: {{[]}}         # from Bank C, e.g. [board-comms, investor-comms, personnel]
  memory_tier_line: default  # sets the Tier-1↔Tier-2 boundary for cold-path writes
```

## Connectors
```yaml
# NAMES + STATUS ONLY. No token/secret/credential/key field is permitted here — secrets live in the
# OS keychain / runtime connector auth (see engine/methods/connectors.md). status: connected | pending |
# verified | blocked. surface: claude-code | codex | cursor | cowork. mechanism: how it was wired.
connectors:
  email:      {status: pending, surface: , mechanism: , scope: , last_verified: }
  calendar:   {status: pending, surface: , mechanism: , scope: , last_verified: }
  recordings: {status: pending, surface: , mechanism: , scope: , last_verified: }
  # add slack / drive / etc. as wired in Step 0
```

## Schedules
```yaml
# Cadence per skill — the runtime-agnostic SOURCE OF TRUTH. If the runtime can't
# schedule natively (see U0 spike (a)), an external launchd/cron driver reads this
# same block. status: live (tool-registered or routine, actually firing) |
# manual (recorded; user must finish a dashboard/UI click) | intent-only (recorded,
# no driver wired yet). registered_via: how it was wired (cron-tool | routine |
# scheduled-task | codex-automation | dashboard | launchd | "" if none).
# A scheduled run still only PROPOSES (drafts to queue/) — never sends outward.
# Times default to the principal's local timezone; adjust at onboarding if asked.
schedules:
  extract-from-sources: {cadence: daily, at: "17:30", status: intent-only, registered_via: "", profile: restricted}   # isolated pass — stages the day's sources BEFORE the consumers below; MUST register with the restricted extractor profile (engine/docs/write-isolation-config.md), never the normal one
  meeting-prep:        {cadence: daily,   at: "17:00", status: intent-only, registered_via: ""}
  meeting-follow-up:   {cadence: daily,   at: "18:00", status: intent-only, registered_via: ""}   # end of day; inverse of prep
  entity-enrichment:   {cadence: daily,   at: "18:30", status: intent-only, registered_via: ""}   # after the 17:30 extract pass it consumes
  loop-closing:        {cadence: weekly,  day: mon,    status: intent-only, registered_via: ""}
  research:            {cadence: weekly,  day: mon,    status: intent-only, registered_via: ""}
  coaching:            {cadence: weekly,  day: fri,    status: intent-only, registered_via: ""}
  system-maintenance:  {cadence: weekly,  day: fri,    status: intent-only, registered_via: ""}
  consolidate-memory:  {cadence: weekly,  day: sun,    status: intent-only, registered_via: ""}   # cold path
  goal-setting:        {cadence: monthly, day: 1,      status: intent-only, registered_via: ""}
```

## Delivery
```yaml
# Where skill output reaches you. Delivery to YOUR OWN file/inbox/DM is a
# notification (inward) — NOT an outward action; sending on your behalf is always
# a proposal. channel: file (default) | email-self | slack-self. Only channels
# whose connector is wired (see connectors:) may be used. Asked at onboarding.
delivery:
  default:            {channel: file, path: "state/briefs/"}
  meeting-prep:       {channel: file, path: "state/briefs/"}
  loop-closing:       {channel: file, path: "state/briefs/"}
  research:           {channel: file, path: "state/briefs/"}
  coaching:           {channel: file, path: "state/briefs/"}
  goal-setting:       {channel: file, path: "state/briefs/"}
  system-maintenance: {channel: file, path: "state/briefs/"}
```

## Loop-closing
```yaml
loop_closing:
  stalled_after_days: 7      # a loop with no movement (open-loops.md Last update) older than this is flagged stalled
```

## Queue lifecycle
```yaml
queue:
  retain_resolved_days: 14   # approved/rejected proposals move to log/ or are deleted after this window
```

## Loop tuning (v1-of-one)
```yaml
write_back:
  decay_weeks: 4             # corrections that never cluster are dismissed after this
  volume_floor: 4            # below this many corrections for a tag, report "insufficient data" not a rate
  source_derived_cap_per_batch: 5   # max source-derived #fact promotions per cold-path batch; overflow defers to next week (oldest-first)
  # thresholds default per engine/methods/write-back.md §3; lower here only if patterns never accrue
```
