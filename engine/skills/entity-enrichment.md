---
skill: entity-enrichment
cadence: daily
kind: ritual
---

# entity-enrichment — keep the world model current

> Keeps `semantic/` (people, accounts, projects, competitors) fresh from recent activity. Load `procedural/` adaptations if present.

## Steps
1. **Find touched entities** from recent captures (`log/runs/`), episodic notes, and new sources.
2. **For each entity:**
   - If it doesn't exist → create from the matching `engine/templates/<type>.md` (set `origin`, `confidence`, `sources`).
   - If it exists and a fact changed → **supersede, don't overwrite** (stamp `valid_until`, append new) — or stage a `#fact` correction for the cold path if it's a real contradiction.
   - Update `last_touched`, `relationships`, `confidence`.
3. **Respect provenance.** Source-derived facts stay `origin: observed`; do not auto-promote to `confirmed`.

## Output
Updated entity files (append-only on the hot path; true contradictions reconciled by the cold path).

## Test scenarios (verification)
- Enriching a non-existent entity creates it from the template with valid frontmatter.
- A changed fact on an existing entity is superseded (prior value still readable with `valid_until`), not overwritten.
- Source-derived facts remain `origin: observed`.

## Capture footer
End with `engine/templates/capture-footer.md`.
