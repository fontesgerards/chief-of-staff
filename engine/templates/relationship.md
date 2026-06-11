---
type: relationship
status: active
last_touched: YYYY-MM-DD
relationships: []         # the two+ entities this describes
confidence: 75
origin: observed          # observed | confirmed | inferred | imported | derived — often `confirmed`; relationships are sensitive, promote at threshold 1
sources: []
sensitivity: normal       # normal | high — high routes any related draft to extra care
---

# {{A}} ↔ {{B}}

**Nature:** one line — how they relate (reports-to, rival, ally, history).

## Sensitivities
- Political context, what to never imply, who is delicate with whom.
- `#relationship` corrections promote here at **threshold 1** — a misread is fixed immediately.

## Facts
- Durable, sourced facts: `{{fact}} (origin, YYYY-MM-DD, source: …)` — superseded facts append `; valid_until: YYYY-MM-DD`.

## History
- Dated events that shaped the relationship (link `[[episodic]]`).
