---
name: consolidate-memory
description: Weekly memory consolidation (the cold path) — promote clustered learnings, supersede stale facts, decay and prune, and produce a reviewable diff. Usually scheduled; the only skill that edits memory.
cadence: weekly            # config.md schedules.consolidate-memory
kind: cold-path
mutates: true             # the ONLY skill allowed to edit/delete memory
---

# consolidate-memory — the cold path

> The **only** place destructive memory edits happen, and only under discipline. Reads the week's captures + corrections and reconciles them into the canonical Markdown. Output is a **reviewable diff in batch** + a changelog + a git commit — you review the diff, never write-by-write. Full algorithm: `engine/methods/write-back.md` §5.

## Inputs
- `instance/state/corrections.md` (status: open)
- `instance/log/runs/*.md` since last consolidation (captures)
- `instance/state/{open-loops,commitments,pending-questions}.md`
- `instance/config.md` → `write_back.*`, `autonomy.memory_tier_line`

## The five operations

1. **Promote** — recurring corrections (same tag ≥ threshold, or any `strength: rule`) become edits to the tag's single write-target (§3 table). *This is the learning.* Apply the §5 algorithm: group → threshold/rule → draft synthesized edit → diversity check → tier-classify.
2. **Merge** — duplicate entities collapse into one canonical file; redirect backlinks.
3. **Supersede, don't overwrite** — a stale fact gets `valid_until` stamped and the new fact appended. History is preserved; you can always see what was true and when.
4. **Decay** — age `last_touched`/`confidence`; flag + archive unreinforced low-confidence facts; dismiss corrections older than `write_back.decay_weeks` that never clustered.
5. **Prune** — move closed loops / resolved questions out of `state/` into `memory/episodic/`.

## Safety tiers (write-back §5.4)
- **Tier 1 (auto + changelog):** merges, supersedes, decay, most `#process`/`#fact` promotions.
- **Tier 2 (propose to queue):** any edit to `core/` (identity/voice/autonomy/priorities), deleting sourced evidence, or carrying **source-derived** content into `procedural`/`core`. Write these to `instance/queue/review/daily-brief-<date>.md` as a **raw diff** (not a summary) for explicit approval.
- `core/` budget pressure: if a promotion would exceed a `core/` file's `budget_chars`, **consolidate/supersede before adding** (a char-count helper flags over-budget; it proposes consolidation, it is not a hard runtime block).

## Health metric + low-volume mode (write-back §7 / §7.1)
- Compute per-tag correction rate with the **deterministic count helper** (group by tag + ISO week); interpret, don't hand-count.
- Below `write_back.volume_floor` for a tag → report **"insufficient data"**, not a rate. Use the **promotion-survival proxy** (did a promoted rule yield zero same-kind corrections after?).
- Weeks 1–4 promoting only via `#fact`/`#relationship`/`rule` is the **planned** early phase.
- **Mistagging check:** flag any tag whose promotions repeatedly fail to reduce recurrence (a wrong *cut* — distinct from the `#other` rate).

## Injection containment at the cold path (write-back §8)
- Provenance is **sticky**; **no source-derived content** reaches `procedural`/`core` without a Tier-2 approval, regardless of recurrence.
- Only restated derived facts are promoted — **never raw source text verbatim**.
- **Bound the review surface:** cap source-derived promotions per batch and segregate source-derived diffs from internal corrections in the daily brief.

## Outputs
1. `instance/log/maintenance/<date>.md` — the changelog (every operation, with before/after + tier).
2. A git commit of `instance/` (the diff is the review surface).
3. Tier-2 proposals appended to `instance/queue/review/daily-brief-<date>.md`.
4. The health report (per-tag rate or "insufficient data", promotion-survival, any mistagging/`#other` flags).
5. Backup commit per `instance/.backup-instructions.md` cadence.

## Verification (a week of seeded captures)
- A single reviewable diff + changelog is produced.
- Nothing in `core/` was edited without a queued Tier-2 proposal.
- A `#fact` correction superseded (not overwrote) its target; prior value still readable with `valid_until`.
- A `strength: rule` correction promoted at count 1; a sub-threshold `#voice` cluster did **not** auto-promote.
- The health report renders; a sub-floor tag shows "insufficient data".

## Capture footer
End with the standard capture footer (`engine/templates/capture-footer.md`) — yes, even the cold path captures its own run for observability.
