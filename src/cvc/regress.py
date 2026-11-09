"""Step 7 (regression): measure the shock.

A. Interrupted time series (segmented regression), per country:
     CI_t = b0 + b1*t + sum_k [level_k*post_k + slope_k*since_k] + month-of-year FE + ramadan_share_t + e
   Newey-West (HAC) errors for autocorrelation.
   ramadan_share = fraction of the month inside Ramadan. Ramadan moves ~11 days a year and
   Ramadan 2026 (approx. 18 Feb-19 Mar) overlaps the start of the 2026 conflict, so without this
   control the model would credit Ramadan effects to the war.

B. Difference-in-differences, UAE (hit by the 2026 conflict) vs UK (not directly hit):
     CI_ct = country FE + month FE + UAE-specific linear trend (common trend is absorbed by month FE) + ramadan + delta*(UAE x post) + e
   Event study shows the UAE-UK gap month by month around March 2026.
   Two units only: a comparative case study, not a large-sample causal estimate.

Every model is run on two versions of the index:
   main         - all index terms
   english_only - English terms only (UAE Arabic deal searches are in long decline, a language shift)
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from . import DATA, OUTPUTS, load_yaml
from .index import certainty_index

# Approximate Ramadan start dates (1 Ramadan; can vary by a day by sighting). ~30 days each.
RAMADAN_START = ["2019-05-06", "2020-04-24", "2021-04-13", "2022-04-02",
                 "2023-03-23", "2024-03-11", "2025-03-01", "2026-02-18"]


def ramadan_share(dates: pd.Series) -> pd.Series:
    days = pd.Series(0.0, index=dates.index)
    for s in RAMADAN_START:
        rng = pd.date_range(s, periods=30, freq="D")
        per_month = rng.to_period("M").value_counts()
        for p, n in per_month.items():
            days[dates.dt.to_period("M") == p] += n / p.days_in_month
    return days


def _prep(ci: pd.DataFrame) -> pd.DataFrame:
    ci = ci.copy()
    ci["date"] = pd.to_datetime(ci["date"])
    ci["moy"] = ci["date"].dt.month
    ci["ramadan"] = ramadan_share(ci["date"])
    return ci


def its(ci: pd.DataFrame, shocks: dict, variant: str) -> pd.DataFrame:
    rows = []
    for country, events in shocks.items():
        if country == "did":
            continue
        d = ci[ci["country"] == country].sort_values("date").reset_index(drop=True)
        if d.empty:
            continue
        d["t"] = np.arange(len(d))
        terms = ["t", "ramadan"]
        for ev in events:
            start = pd.Timestamp(ev["date"])
            d[f"post_{ev['id']}"] = (d["date"] >= start).astype(int)
            terms.append(f"post_{ev['id']}")
            if ev.get("slope", True):
                k0 = d.index[d["date"] >= start]
                k0 = k0[0] if len(k0) else len(d)
                d[f"since_{ev['id']}"] = np.clip(d["t"] - k0, 0, None)
                terms.append(f"since_{ev['id']}")
        m = smf.ols("ci ~ " + " + ".join(terms) + " + C(moy)", data=d).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        ci_ = m.conf_int()
        for name in [x for x in terms if x.startswith(("post_", "since_"))] + ["ramadan"]:
            rows.append({
                "variant": variant, "country": country,
                "term": name.split("_", 1)[-1] if name != "ramadan" else "ramadan",
                "effect": "level jump" if name.startswith("post_") else ("trend change / month" if name.startswith("since_") else "per full Ramadan month"),
                "coef": m.params[name], "ci_low": ci_.loc[name, 0], "ci_high": ci_.loc[name, 1], "p": m.pvalues[name],
                "r2": m.rsquared,
            })
    return pd.DataFrame(rows).round(4)


def did(ci: pd.DataFrame, spec: dict, variant: str, pre_months: int = 26):
    post_start = pd.Timestamp(spec["post_start"])
    d = ci[ci["country"].isin([spec["treated"], spec["control"]])].copy()
    d = d[d["date"] >= post_start - pd.DateOffset(months=pre_months)].copy()
    d["treated"] = (d["country"] == spec["treated"]).astype(int)
    d["treat_post"] = d["treated"] * (d["date"] >= post_start).astype(int)
    d["t"] = (d["date"].dt.year - d["date"].dt.year.min()) * 12 + d["date"].dt.month
    d["ram_t"] = d["ramadan"] * d["treated"]   # Ramadan matters for the UAE series
    m = smf.ols("ci ~ C(country) + C(date) + treated:t + ram_t + treat_post", data=d).fit(
        cov_type="HAC", cov_kwds={"maxlags": 3})
    summary = pd.DataFrame([{
        "variant": variant, "estimate": "UAE x post-Mar-2026 (delta)", "coef": m.params["treat_post"],
        "ci_low": m.conf_int().loc["treat_post", 0], "ci_high": m.conf_int().loc["treat_post", 1],
        "p": m.pvalues["treat_post"], "pre_months": pre_months, "post_months": int((d["date"] >= post_start).sum() / 2),
    }]).round(4)
    d["rel"] = ((d["date"].dt.year - post_start.year) * 12 + d["date"].dt.month - post_start.month).astype(int)
    wide = d.pivot_table(index="rel", columns="country", values="ci")
    gap = wide[spec["treated"]] - wide[spec["control"]]
    pre_mean = gap[gap.index < 0].mean()
    es = (gap - pre_mean).rename("gap_vs_pre_mean").reset_index()
    es["variant"] = variant
    return summary, es


def main():
    shocks = load_yaml("shocks.yaml")
    rel = pd.read_csv(DATA / "processed" / "trends_relative.csv", parse_dates=["date"])
    arabic = rel["term"].map(lambda t: bool(re.search("[؀-ۿ]", t)))
    variants = {"main": certainty_index(rel), "english_only": certainty_index(rel[~arabic])}
    t = OUTPUTS / "tables"
    its_all, did_all, es_all = [], [], []
    for v, ci in variants.items():
        ci = _prep(ci)
        ci.to_csv(DATA / "processed" / f"certainty_index_{v}.csv", index=False)
        its_all.append(its(ci, shocks, v))
        s, es = did(ci, shocks["did"], v)
        did_all.append(s)
        es_all.append(es)
    a = pd.concat(its_all)
    a.to_csv(t / "its_results.csv", index=False)
    s = pd.concat(did_all)
    s.to_csv(t / "did_results.csv", index=False)
    pd.concat(es_all).to_csv(t / "event_study.csv", index=False)
    pd.set_option("display.width", 200)
    print("\nInterrupted time series\n", a.to_string(index=False))
    print("\nDifference-in-differences (UAE vs UK, 2026)\n", s.to_string(index=False))


if __name__ == "__main__":
    main()
