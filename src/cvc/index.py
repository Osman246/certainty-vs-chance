"""Step 2: build the Certainty Index from search interest.

For each term:   rel_t = ln( (interest_t + 1) / (mean interest in baseline year + 1) )
                 -> 0 means "same as 2019", +0.69 means "double 2019", -0.69 means "half".
For each side:   the average rel_t of its terms (chance side, certainty side).
Certainty Index: CI_t = certainty_t - chance_t
A rising CI means attention to guaranteed rewards grew faster than attention to prizes.

Also outputs the Aug-Nov seasonal table, which is how promotions businesses compare years.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import DATA, OUTPUTS, load_yaml


def load_trends() -> pd.DataFrame:
    p = DATA / "raw" / "trends_long.csv"
    if not p.exists():
        raise FileNotFoundError("No data/raw/trends_long.csv. Run the collector first.")
    df = pd.read_csv(p, parse_dates=["date"])
    cfg = load_yaml("terms.yaml")["countries"]
    meta = {(c, t["term"]): t for c, s in cfg.items() for t in s["terms"]}
    df["side"] = [meta.get((c, t), {}).get("side", "excluded") for c, t in zip(df["country"], df["term"])]
    df["circle"] = [meta.get((c, t), {}).get("circle", "") for c, t in zip(df["country"], df["term"])]
    return df


def relative(df: pd.DataFrame, baseline_year: int) -> pd.DataFrame:
    base = df[df["date"].dt.year == baseline_year].groupby(["country", "term"])["interest"].mean().rename("base")
    df = df.join(base, on=["country", "term"])
    df["rel"] = np.log((df["interest"] + 1) / (df["base"] + 1))
    return df


def certainty_index(df: pd.DataFrame, drop_terms: tuple = ()) -> pd.DataFrame:
    d = df[df["side"].isin(["certainty", "chance"]) & ~df["term"].isin(drop_terms)]
    s = d.groupby(["country", "date", "side"])["rel"].mean().unstack("side").reset_index()
    s["ci"] = s["certainty"] - s["chance"]
    return s.sort_values(["country", "date"]).reset_index(drop=True)


def seasonal_table(ci: pd.DataFrame, months: list[int]) -> pd.DataFrame:
    s = ci[ci["date"].dt.month.isin(months)].copy()
    s["year"] = s["date"].dt.year
    out = s.groupby(["country", "year"])[["chance", "certainty", "ci"]].mean().round(3)
    return out.reset_index()


def main():
    cfg = load_yaml("terms.yaml")
    w = cfg["window"]
    df = relative(load_trends(), w["baseline_year"])
    df.to_csv(DATA / "processed" / "trends_relative.csv", index=False)
    ci = certainty_index(df)
    ci.to_csv(DATA / "processed" / "certainty_index.csv", index=False)
    # robustness: without the noisiest terms
    certainty_index(df, drop_terms=("سحب", "win", "win a")).to_csv(DATA / "processed" / "certainty_index_robust.csv", index=False)
    tbl = seasonal_table(ci, w["season_months"])
    tbl.to_csv(OUTPUTS / "tables" / "seasonal_aug_oct.csv", index=False)
    print(tbl.pivot(index="year", columns="country", values="ci").to_string())


if __name__ == "__main__":
    main()
