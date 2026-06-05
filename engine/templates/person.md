---
type: person
status: active            # active | dormant | former
last_touched: YYYY-MM-DD
relationships: []         # [[entity-name]] links — accounts, projects, other people
confidence: 75            # 0 | 25 | 50 | 75 | 100
origin: observed          # observed | confirmed | inferred | imported
sources: []               # backlinks into memory/sources/
role:                     # their role / title
org:                      # [[account]] they belong to
---

# {{Name}}

**Who:** one line — role, org, why they matter to the principal.

## Context
- What the principal is working on with them.
- Sensitivities / political context → link the `[[relationship]]` file rather than inlining.

## Facts
- Durable, sourced facts. Each can carry inline `(origin, valid_until)` when superseded.

## Open with them
- Open loops, commitments, next step.
