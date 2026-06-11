---
type: consolidation-changelog
date: YYYY-MM-DD          # filename: log/maintenance/YYYY-MM-DD.md
origin: derived           # observed | confirmed | inferred | imported | derived
---

# Consolidation — {{date}}

## Operations (the changelog)
> Every edit, with before→after + tier. One line each; grouped by operation.
- **Promote** · `#tag` → `<target>` · {{what changed}} · Tier {{0|1|2}}
- **Merge** · `<dupe>` → `<canonical>` · Tier 1
- **Supersede** · `<entity>.<fact>` old→new (`valid_until` stamped) · Tier 1
- **Decay** · `<fact/correction>` aged/archived/dismissed · Tier 1
- **Prune** · `<loop/question>` state/ → episodic/ · Tier 1

## Review surface (no-git)
> Only on instances without git (the `runtime:` row's `git` ≠ `verified`). With git, the commit diff is the review surface — omit this section.
- **Snapshot:** `<instance>-snapshots/{{YYYY-MM-DD}}/` (taken before any edit; expired `sources/` pruned first; retention 3)
- **Changed:** {{files edited}}
- **Added:** {{files created}}
- **Deleted:** {{files removed}}

## Health report
> Read by `cos-system-maintenance`. Keep the table shape stable.

| Tag | Corrections (ISO wk) | Rate / status | Trend vs last wk |
|---|---|---|---|
| `#voice` | {{n}} | {{rate \| insufficient-data}} | {{↓ \| ↑ \| → }} |
| … | | | |

- **Promotion-survival:** {{which promoted rules produced zero same-kind corrections after}}
- **Mistagging flags:** {{tags whose promotions didn't reduce recurrence, or "none"}}
- **`#other` rate:** {{n}} {{— propose new tag? if ≥2}}
- **Source-derived cap:** {{applied N/5 · M deferred to next week | not hit}}

## Tier-2 proposals
- {{count}} raw-diff(s) appended to `queue/review/review-<date>.md` for approval. (Listed there, not here.)
