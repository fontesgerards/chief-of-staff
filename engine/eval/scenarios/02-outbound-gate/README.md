# Scenario 02 — the outward-action gate

**What it exercises:** the mechanism that makes `INSTRUCTIONS.md` §1 ("propose,
never act") *structural* instead of behavioral — the outward twin of the memory
provenance guard. If it stays green, the agent **cannot** execute an outward
connector call that isn't a payload-matched approved proposal at a permissive
dial. Deterministic, no LLM (`engine/methods/write-back.md` §8.2).

Plan: `docs/plans/2026-06-10-001-feat-outward-action-gate-plan.md`.
Brainstorm: `docs/brainstorms/2026-06-10-outward-action-gate-requirements.md`.

## Why the assertions live in pytest, not `expected.yaml`

The structural runner (`run_scenario.py`) asserts **memory file-state** a model
run produces. The gate produces no file-state — its contract is the **exit code**
of a `PreToolUse` hook (0 = allow, 2 = deny). So the executable end-to-end
assertions live in the pytest suites, which invoke the real hook as a subprocess:

- `engine/eval/hooks/test_outbound_gate.py` — the hook contract (exit codes).
- `engine/eval/lib/test_outbound.py` — canonicalization, digest, matching, tokens, dial parsing.

Both run in CI alongside the structural scenarios (`.github/workflows/eval.yml`):

```bash
python3 -m pytest engine/eval -q
```

## The invariants under test

| Invariant | Requirement | Covered by |
|---|---|---|
| Outward call with no matching proposal → **deny** | R1 | `test_outward_call_without_proposal_denied` |
| One approval authorizes exactly one action; edit → re-queue | R2 | `test_edited_proposal_fails_match` |
| Irreversible action allowed once, replay denied (token burned) | R3 | `test_irreversible_allowed_once_then_denied` |
| Matched call denied at the default `propose-only` dial | R4 | `test_matched_but_propose_only_denied` |
| Unreadable config / queue / dial → deny | R5 | `test_missing_config_denied`, lib `GateError` tests |
| Read verbs (`list_`/`get_`/`search_`) pass untouched | R6 | `test_read_verb_allowed` |
| Denial feedback names the proposal route (self-correct) | R9 | `test_outward_call_without_proposal_denied` |
| Memory provenance scenario (01) unchanged | R10 | scenario 01 stays green |

## The honest limit (carried from the plan)

The gate watches **MCP tool names**. It does not watch `Bash` (`curl`,
`osascript`) — that egress is closed by the OS sandbox (layer 3), and read-only
OAuth scopes (layer 1) are the cross-platform floor. The hook is layer 2:
necessary, not sufficient on its own. See the plan's *Cross-Surface Enforcement*
and `engine/docs/write-isolation-config.md`.
