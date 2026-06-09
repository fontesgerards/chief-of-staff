# Turn 1 — week of 2026-05-12

Inputs fed to the agent this week (drives runs + end-of-week consolidation):

1. Meeting follow-up where the agent calls Andre "VP Engineering".
   Principal correction: "Andre is our CTO, not VP Eng."
   → expect a #fact correction (entity people/andre-maligian).
2. A recap drafted with a formal preamble.
   Principal correction: "cut the preamble, get to the ask."
   → expect a #voice nudge.

Expected after consolidation:
- #fact promotes at threshold 1 → andre's role superseded to CTO (old value retained, valid_until stamped).
- #voice cluster size 1 → NOT promoted.
