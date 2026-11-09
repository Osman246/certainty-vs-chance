"""Step 1: collect monthly Google Trends interest, ONE TERM PER REQUEST.

Why one term per request: Google scales a multi-term request to its largest term and rounds to
whole numbers, so small terms ("prize draw") come back as 0 beside big ones ("discount code").
Each term is therefore fetched alone (0-100 on its own scale) and the analysis uses each term's
change against its own 2019 level (see index.py).

    python -m cvc.collect_trends            # writes data/raw/trends_long.csv
Google rate-limits scripted access heavily; the script pauses between requests. The v1 data was
collected the same way through the Trends website's own endpoint (see docs/data_collection.md).
"""
from __future__ import annotations

import random
import time

import pandas as pd

from . import DATA, load_yaml


def fetch_term(py, term: str, geo: str, timeframe: str) -> pd.Series:
    py.build_payload([term], timeframe=timeframe, geo=geo)
    df = py.interest_over_time()
    if df.empty:
        raise RuntimeError(f"no data for {term!r} in {geo}")
    return df[term].astype(int).resample("MS").mean().round().astype(int)


def main(sleep: float = 15.0):
    from pytrends.request import TrendReq

    cfg = load_yaml("terms.yaml")
    w = cfg["window"]
    py = TrendReq(hl="en-GB", tz=0, timeout=(10, 30), retries=3, backoff_factor=2)
    rows = []
    for code, spec in cfg["countries"].items():
        for t in spec["terms"]:
            s = fetch_term(py, t["term"], spec["geo"], f"{w['start']} {w['end']}")
            rows += [{"date": d.date(), "country": code, "term": t["term"], "interest": int(v)} for d, v in s.items()]
            print(f"  {code} {t['term']}: {len(s)} months")
            time.sleep(sleep + random.uniform(0, 5))
    out = DATA / "raw" / "trends_long.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
