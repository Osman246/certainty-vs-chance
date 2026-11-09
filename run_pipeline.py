"""Rebuild every table and chart from the raw data in data/raw/.

    python run_pipeline.py

Raw data (already collected, see docs/data_collection.md):
  data/raw/trends_long.csv            monthly Google Trends, 32 terms, UK + UAE, Jan 2019 - Oct 2026
  data/raw/related_rows_compact.txt   Google related queries, 8 seeds x 8 years x 2 countries
  data/labels/query_labels_claude_compact.txt   Claude's labels for the 669 unique queries
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
steps = ["cvc.index", "cvc.regress", "cvc.placebo", "cvc.robustness",
         "cvc.parse_related", "cvc.label_queries", "cvc.ml_queries", "cvc.charts"]
env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONWARNINGS": "ignore"}
for s in steps:
    print(f"\n=== {s} ===", flush=True)
    subprocess.run([sys.executable, "-m", s], check=True, cwd=ROOT, env=env)
