---
type: loop-closing-brief
date: YYYY-MM-DD          # filename: state/briefs/loop-closing-YYYY-MM-DD.md
origin: derived           # observed | confirmed | inferred | imported | derived
---

# Open loops — {{date}}

## Unassigned (no owner)
- **{{loop/commitment}}** → suggested owner: {{who}} · next: {{step}}

## Stalled (no movement > {{stalled_after_days}}d)
- **{{loop}}** (last update {{date}}) → next: {{step}}

## Overdue (past due)
- **{{commitment}}** — owed by {{who}}, due {{date}} → next: {{step}}

## Going quiet (key relationships, no contact > {{relationship_stale_after_days}}d)
- **[[{{person}}]]** — last real contact {{date}} ({{meeting | sent reply}}) → suggested touch: {{step}}

## Queued nudges
- {{count}} outward nudge(s) drafted to `queue/outbound/` for your approval (in your voice). (Exact text lives there, not here.)
