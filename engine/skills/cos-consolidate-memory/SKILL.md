---
name: cos-consolidate-memory
description: Weekly memory consolidation (the cold path) — promote clustered learnings, supersede stale facts, decay and prune, and produce a reviewable diff. Usually scheduled; the only skill that edits memory.
cadence: weekly            # config.md schedules.consolidate-memory
kind: cold-path
mutates: true             # the ONLY skill allowed to edit/delete memory
---

# consolidate-memory — the cold path

> The **only** place destructive memory edits happen, and only under discipline. Reads the week's captures + corrections and reconciles them into the canonical Markdown. Output is a **reviewable diff in batch** + a changelog + a git commit (or, without git, a dated snapshot + before/after file list — "Review surface" below) — you review the batch, never write-by-write. Full algorithm: `engine/methods/write-back.md` §5.

## Inputs
- `instance/state/corrections.md` (status: open)
- `instance/log/runs/*.md` since last consolidation (captures)
- `instance/state/{open-loops,commitments,pending-questions}.md`
- `instance/state/validation/findings-*.md` (latest — the weekly sweep's manifest; see "Consume validation findings")
- `instance/config.md` → `write_back.*`, `autonomy.memory_tier_line`

## The five operations

1. **Promote** — recurring corrections (same tag ≥ threshold, or any `strength: rule`) become edits to the tag's single write-target (§3 table). *This is the learning.* Apply the §5 algorithm: group → threshold/rule → draft synthesized edit → diversity check → tier-classify.
2. **Merge** — duplicate entities collapse into one canonical file; redirect backlinks.
3. **Supersede, don't overwrite** — a stale fact gets `valid_until` stamped and the new fact appended. History is preserved; you can always see what was true and when.
4. **Decay** — age `last_touched`/`confidence`; flag + archive unreinforced low-confidence facts; dismiss corrections older than `write_back.decay_weeks` that never clustered. **Never decay/archive continuity records** — `episodic/coaching/` and `episodic/goals/` are read by their skills' *next* run; they are dated narrative, not scored facts, and stay readable indefinitely.
5. **Prune** — move closed loops / resolved questions out of `state/` into `memory/episodic/`.

## Consume validation findings (the sweep's fixer — KTD7)

The weekly `cos-system-maintenance` sweep (`engine/validate_instance.py`) writes `state/validation/findings-<date>.md` but never fixes anything; **this** run is where findings get fixed.

1. Read the **latest** `state/validation/findings-*.md`. Each line carries a stable fingerprint, severity, file, check, detail, and `first_seen:`.
2. **Re-run the finding's deterministic check against the current file first** — the manifest may be days stale and the file may have changed since the sweep. If it no longer reproduces, **skip it and log "resolved before fix"** in the changelog (never "fix" a defect that's already gone).
3. Tier-classify what still reproduces:
   - **Mechanical frontmatter fixes** (missing/renamed required keys, an `origin` outside the closed enum with an unambiguous correct value, a dangling-wikilink rename) → **Tier 1**: apply + changelog entry.
   - **Anything touching `core/` or changing fact content** → **Tier 2**: raw diff to `queue/review/review-<date>.md` for approval.
4. **Fingerprint dedup:** a fingerprint already actioned and still open (a Tier-2 proposal pending approval) is **not re-proposed** — note it in the changelog as "open, awaiting approval" and move on.

## Review surface — before any destructive edit (KTD8)

Branch on this host's `runtime:` row (`git` state) **before the first destructive edit**:

- **Git `verified`:** the existing flow stands — the batch lands as a git commit of `instance/`; the diff is the review surface.
- **No git (`unavailable`/`unverified`):** a snapshot is **mandatory first** — never edit-then-snapshot:
  1. **Prune expired `sources/` items first** (`retention_until` past ⇒ delete) *before* copying — pruned PII must never persist into a snapshot; snapshots inherit `sources/` pruning.
  2. Copy `instance/` → sibling `<instance>-snapshots/<YYYY-MM-DD>/` (the snapshot dir lives beside the instance, never inside it, and is excluded from its own snapshots).
  3. Apply retention 3: delete the oldest snapshot(s) beyond three.
  4. Then edit, and write the **before/after file list** (changed/added/deleted, plus the snapshot path) into the changelog's "Review surface (no-git)" section — that list is the review surface where there is no diff.

The one-time schema migration runs through this skill and follows the same snapshot-first rule.

## Safety tiers (write-back §5.4)
- **Tier 1 (auto + changelog):** merges, supersedes, decay, most `#process`/`#fact` promotions.
- **Tier 2 (propose to queue):** any edit to `core/` (identity/voice/autonomy/priorities), deleting sourced evidence, or carrying **source-derived** content into `procedural`/`core`. Write these to `instance/queue/review/review-<date>.md` as a **raw diff** (not a summary) for explicit approval.
- `core/` budget pressure: if a promotion would exceed a `core/` file's `budget_chars`, **consolidate/supersede before adding** (a char-count helper flags over-budget; it proposes consolidation, it is not a hard runtime block).

## Health metric + low-volume mode (write-back §7 / §7.1)
- Compute per-tag correction rate with the **deterministic count helper** (group by tag + ISO week); interpret, don't hand-count.
- Below `write_back.volume_floor` for a tag → report **"insufficient data"**, not a rate. Use the **promotion-survival proxy** (did a promoted rule yield zero same-kind corrections after?).
- Weeks 1–4 promoting only via `#fact`/`#relationship`/`rule` is the **planned** early phase.
- **Mistagging check:** flag any tag whose promotions repeatedly fail to reduce recurrence (a wrong *cut* — distinct from the `#other` rate).

## Injection containment at the cold path (write-back §8)
- Provenance is **sticky**; **no source-derived content** reaches `procedural`/`core` without a Tier-2 approval, regardless of recurrence.
- Only restated derived facts are promoted — **never raw source text verbatim**.
- **Bound the review surface:** cap source-derived promotions at `write_back.source_derived_cap_per_batch` (default 5) **per batch** — this now matters because daily `cos-entity-enrichment` and weekly `cos-research` stage source-derived `#fact` corrections, which promote at threshold 1. Overflow **defers to next week, logged** (oldest-first), so one noisy week can't bloat the batch diff. Segregate source-derived diffs from internal corrections in the review surface.

## Outputs
1. `instance/log/maintenance/<date>.md` from `engine/templates/consolidation-changelog.md` — the changelog (every operation, before/after + tier) **and** the health report. Keep the health-report table shape stable: `cos-system-maintenance` machine-reads it.
2. A git commit of `instance/` where git is `verified` (the diff is the review surface); otherwise the dated snapshot + the changelog's before/after file list ("Review surface" above).
3. Tier-2 proposals appended to `instance/queue/review/review-<date>.md`.
4. The health report **is the §Health report section** of that maintenance file (per-tag rate or "insufficient data", promotion-survival, mistagging/`#other` flags, source-derived-cap status) — not a separate file.
5. Backup commit per `instance/.backup-instructions.md` cadence.

## Verification (a week of seeded captures)
- A single reviewable diff + changelog is produced.
- Nothing in `core/` was edited without a queued Tier-2 proposal.
- A `#fact` correction superseded (not overwrote) its target; prior value still readable with `valid_until`.
- A `strength: rule` correction promoted at count 1; a sub-threshold `#voice` cluster did **not** auto-promote.
- The health report renders; a sub-floor tag shows "insufficient data".
- **Continuity carve-out:** a week-old `episodic/coaching/` (or `episodic/goals/`) note is **not** decayed or archived — it remains readable by the next coaching/goal-setting run.
- **Source-derived cap:** a batch with more than `source_derived_cap_per_batch` source-derived `#fact` promotions applies the cap, defers the overflow to next week (logged, oldest-first), and does not bloat the single review diff.
- **Validation findings:** a stale finding whose check no longer reproduces is skipped and logged "resolved before fix"; a reproducing mechanical fix lands as Tier 1; a reproducing `core/`-touching fix is a Tier-2 proposal; a fingerprint with a pending Tier-2 proposal is not re-proposed.

## Output contract
| Artifact | Template | Path | Required frontmatter |
|---|---|---|---|
| changelog + health report | `engine/templates/consolidation-changelog.md` | `log/maintenance/YYYY-MM-DD.md` | `type`, `date`, `origin` |
| capture footer | `engine/templates/capture-footer.md` | `log/runs/<date>-<run>.md` | (appended block) |

Tier-2 proposals are raw diffs appended to `queue/review/review-<date>.md` (no frontmatter schema); memory edits follow the edited file's own type contract (`engine/eval/lib/schema.py`).

## Capture footer
End with the standard capture footer (`engine/templates/capture-footer.md`) — yes, even the cold path captures its own run for observability.
