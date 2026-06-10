"""Put engine/eval on sys.path so tests import the harness packages the same way
run_scenario.py / run_all.py do (`from lib import ...`)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
