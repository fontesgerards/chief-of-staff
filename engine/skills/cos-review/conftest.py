import sys
from pathlib import Path

# Make the skill's scripts importable as top-level modules in tests, regardless
# of pytest's rootdir.
HERE = Path(__file__).resolve().parent
EVAL_LIB = HERE.parents[1] / "eval" / "lib"   # frontmatter + outbound (the gate's contract)
for p in (str(HERE), str(EVAL_LIB)):
    if p not in sys.path:
        sys.path.insert(0, p)
