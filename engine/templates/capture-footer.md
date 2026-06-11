# Capture footer — append at the END of every skill run

> Strictly **append-only**. Never edits or deletes existing memory. Writes timestamped, sourced, `origin`-tagged entries to `instance/state/` and `instance/log/runs/<run>.md`. Reconciliation is the cold path's job, not yours. Because nothing is destroyed, a bad capture cannot silently corrupt the brain.

```
## Capture — <skill> — <YYYY-MM-DDTHH:MM±HH:MM>   # principal-local offset; UTC (+00:00) when unknown
trigger:      scheduled | interactive   # if scheduled, add registered_via: <how it was wired> — feeds the schedule-liveness check
facts:        [{claim, entity, confidence, origin, source}]   # origin: observed|confirmed|inferred|imported|derived
entities:     [people / accounts / projects touched]
loops:        opened: [...]   closed: [...]
commitments:  [{who, what, due, source}]
corrections:  [{what_I_did, what_you_wanted, delta, tags:[...], strength, entity?, source}]
```

Capture policy:
- Write **durable, reusable** facts; derive semantic/episodic memory *from* sources, don't copy sources verbatim; never write transient chatter.
- When unsure whether a fact is durable, capture it **low-confidence** and let decay sort it out.
- `loops`/`commitments` append to `state/open-loops.md` / `state/commitments.md`; `corrections` append to `state/corrections.md` (see `engine/methods/write-back.md` §2).
- If the principal **accepted** output unchanged, record it as positive signal (reinforce confidence on facts used) — **not** a correction.
- Append a one-line run entry to `instance/log/runs/<run>.md` for observability.
