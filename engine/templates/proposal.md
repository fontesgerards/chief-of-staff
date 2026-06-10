---
type: proposal
created: YYYY-MM-DD
skill:                   # the run that produced it
status: pending          # pending | approved | rejected | sent
reversibility: reversible   # reversible | irreversible
tool:                    # outward MCP tool this authorizes, e.g. mcp__claude_ai_Google_Calendar__create_event. Blank = principal-only send (the gate never auto-executes it).
args_digest:             # SHA-256 of the canonicalized Action args below. Regenerate (engine/eval/lib/outbound.py: digest) whenever the action changes — a stale digest fails the gate match by design.
---

# Proposal: {{one-line what}}

- **What:** the action (send / post / schedule / update).
- **To whom:** recipient(s) / system.
- **Exact text / payload:**

> The exact content that would go out. The principal approves *this text*, edits it (→ a correction), or rejects it. Nothing is sent until `status: approved` AND the autonomy dial permits, or the principal sends it themselves.

- **Why:** the reasoning / trigger.
- **Reversibility:** reversible | irreversible (irreversible always needs explicit approval regardless of dial).

## Action (machine-readable — the outward-action gate matches against this)

> The exact arguments the outward tool would be called with. The gate (`engine/eval/hooks/outbound_gate.py`) canonicalizes the *live* tool call, digests it, and allows the call only when it matches an `approved` proposal whose `tool` and `args_digest` agree. Edit these args and the digest must be regenerated, or the gate re-queues the action. Leave empty for principal-only sends.

```json
{}
```
