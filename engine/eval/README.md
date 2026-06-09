# engine/eval — the evaluation harness

> Borrowed discipline from [pm-brain](https://github.com/phuryn/pm-brain)'s test
> suite, adapted to *our* differentiator: the write-back learning loop. Our
> claim is "gets sharper the longer it runs" — this is how we keep that honest.

## Why this exists

Until now our "Test scenarios" lived as prose at the bottom of each `SKILL.md`.
Nothing ran them. This harness makes the invariants in `engine/methods/write-back.md`
and `engine/INSTRUCTIONS.md` **executable**, so a refactor that quietly breaks
supersede-don't-overwrite, the Tier-2 gate, or injection containment fails loudly.

Two design rules, both from prior art:

1. **Trajectory over time, not single-step output.** A scenario is a *longitudinal
   stream* of weekly inputs, with the brain's state asserted at the end. The thing
   we sell is convergence; the thing we test is convergence.
2. **Don't pay an LLM to do what an assertion can.** Structural truths (a file
   exists, frontmatter has a valid `origin`, history was preserved, a link
   resolves, core/ wasn't touched) are deterministic Python. The LLM-as-judge
   phase is reserved for genuine semantic judgment and is declared with `judge:`.

## Three layers (one built, two scaffolded)

| Layer | What | Status |
|---|---|---|
| **In-loop** | `hooks/provenance_check.py` — PostToolUse guard validating provenance + links at write time (BLOCK/WARN) | **built** |
| **Structural** | `run_scenario.py` / `run_all.py` — deterministic assertions over an instance dir | **built** |
| **Content** | `judge:` assertions for semantic checks (LLM-as-judge), run by a manual Claude Code session on your **subscription** — never the API, never CI | **built** (see `JUDGING.md`) |

## Run it

```bash
pip install -r engine/eval/requirements.txt        # PyYAML (dev only)
python3 engine/eval/run_all.py                      # all scenarios → scorecard, CI exit code
python3 engine/eval/run_scenario.py 01-write-back-loop          # one scenario (validates golden/)
python3 engine/eval/run_scenario.py 01-write-back-loop --instance ./run-output --json
```

`run_all.py` exits non-zero on any structural failure — wire it straight into CI.

## Scenario format

```
scenarios/<NN-slug>/
├── README.md        # what longitudinal behavior it exercises (the turns table)
├── turns/           # ordered weekly inputs — the stream fed to the agent
│   ├── week-1.md
│   └── …
├── golden/          # end-state snapshot a CORRECT run produces (stands in for instance/)
│   ├── memory/  state/  queue/  log/  …
└── expected.yaml    # ground-truth assertions (paths relative to the instance under test)
```

`expected.yaml` shape:

```yaml
turns: [week-1, week-2, …]      # documentation of the stream order
final:                          # assertions against the instance dir
  - desc: human-readable intent
    <check>: <params>
```

### Structural checks (`lib/assertions.py`)

| Check | Params | Asserts |
|---|---|---|
| `file_exists` / `file_absent` | `path` | presence / absence |
| `contains` / `not_contains` | `{path, text, ci?}` | substring present / absent |
| `regex` | `{path, pattern, ci?}` | multiline (DOTALL) regex matches |
| `frontmatter_eq` | `{path, key, value}` | a frontmatter field equals a value |
| `has_origin` | `path` | entity frontmatter has a valid `origin` (closed set) |
| `superseded` | `{path, new, old}` | new + old values both present **and** `valid_until` stamped |
| `valid_links` | `path` | every `[[wikilink]]` resolves to a real `*.md` |
| `judge` | `{prompt, expect}` | content phase — **skipped** by the structural runner |

## The hook

`hooks/provenance_check.py` is a `PostToolUse` guard on `Write|Edit|MultiEdit`.
For any path under `instance/memory/` it:

- **BLOCKs** (exit 2, feedback to the model) an entity file with a missing/invalid
  `origin`, and an edit to `core/` unless `COS_TIER2_APPROVED=1` is set (the approved
  cold-path run sets it).
- **WARNs** (exit 0) on an unresolved `[[wikilink]]` — it may resolve on a later write.

Wire it by copying the block in `hooks/settings.example.json` into your instance's
`.claude/settings.json`. PostToolUse is *corrective* (it fires after the write); to
make the core/ ban *preventive*, pair it with the PreToolUse deny in
`engine/docs/write-isolation-config.md`.

## Content / judge phase

The semantic checks (`judge:` items in `expected.yaml`) are run **manually inside a
Claude Code session** — the agent in the session is the judge, so it uses your
subscription, not API tokens, and never runs in CI. `run_scenario.py --emit-judge`
deterministically prepares the worklist (resolves rubrics + reads artifacts); it has
no code path that calls a model, which is what keeps CI structural-by-construction.
Full procedure: **`JUDGING.md`**.

```bash
python3 engine/eval/run_scenario.py 01-write-back-loop --emit-judge   # prep worklist
# then, in Claude Code: "Run the eval judge on 01-write-back-loop"
```

Add `runs:`/`threshold:` to a `judge:` item to request sampled judging with a
pass-rate bar (pm-brain convention: structural 1.0, content ≥0.8).

## Roadmap

- **Agent driver:** an optional orchestrator that runs the agent through `turns/` to
  produce a real instance dir, then grades it with `--instance` (needs the live runtime;
  the structural layer here grades whatever output you point it at).
- **More scenarios:** meeting-prep retrieval scope, loop-closing ownership, consolidation
  decay/budget pressure.
