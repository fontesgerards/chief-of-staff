---
type: account
status: prospect          # prospect | customer | partner | churned | dormant
last_touched: YYYY-MM-DD
relationships: []         # [[people]], [[projects]], [[competitors]]
confidence: 75
origin: observed          # observed | confirmed | inferred | imported | derived
sources: []
segment:                  # e.g. bank | credit-union | fintech | BPO
stage:                    # pipeline stage if applicable
---

# {{Account}}

**Who:** one line — what they are, why they matter.

## Context
- Current engagement, value, timeline.
- Key people → `[[person]]` links.

## Facts
- Durable, sourced facts (size, pain, constraints, decisions): `{{fact}} (origin, YYYY-MM-DD, source: …)` — superseded facts append `; valid_until: YYYY-MM-DD`.

## Open
- Open loops, commitments, next step, risks.
