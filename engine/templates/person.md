---
type: person
status: active            # active | dormant | former
last_touched: YYYY-MM-DD  # recency — any mention bumps it (all entities); enrichment staleness is last_enriched/enrich below (person-only)
relationships: []         # [[entity-name]] links — accounts, projects, other people
confidence: 75            # 0 | 25 | 50 | 75 | 100
origin: observed          # observed | confirmed | inferred | imported | derived
sources: []               # backlinks into memory/sources/
role:                     # their role / title
org:                      # [[account]] they belong to
last_enriched:            # YYYY-MM-DD of the last web-enrichment pass — distinct from last_touched (which any mention bumps). Blank = never enriched. Drives the staleness gate in cos-entity-enrichment.
enrich:                   # blank/true = eligible for web enrichment; false = opt out (never web-searched)
key:                      # true = a key relationship cos-loop-closing watches for staleness ("going quiet"); blank/false = not watched. Opt-in: seeded at onboarding or promoted by a correction.
last_contacted:           # YYYY-MM-DD of the last REAL contact — stamped by cos-inbox-sweep (principal answered their thread, or a sent draft). Distinct from last_touched: a brief mentioning them is not contact.
---

# {{Name}}

**Who:** one line — role, org, why they matter to the principal.

## Context
- What the principal is working on with them.
- Sensitivities / political context → link the `[[relationship]]` file rather than inlining.

## Facts
- Durable, sourced facts: `{{fact}} (origin, YYYY-MM-DD, source: …)` — superseded facts append `; valid_until: YYYY-MM-DD`.

## Open with them
- Open loops, commitments, next step.
