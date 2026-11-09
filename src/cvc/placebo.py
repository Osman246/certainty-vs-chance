"""Robustness: placebo shocks.

Moves a fake shock to every month in a window where nothing special happened and records the
'level jump' it finds. If the real shock's jump sits far outside the placebo distribution,
it's unlikely to be ordinary month-to-month noise.
Placebo windows end 12 months before the real 2026 shock so they never overlap it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from . import DATA, OUTPUTS
from .regress import _prep


def level_jump(d: pd.DataFrame, start: pd.Timestamp, controls: list[pd.Timestamp]) -> float:
    d = d.copy()
    d["t"] = np.arange(len(d))
    terms = ["t", "ramadan", "post_x"]
    d["post_x"] = (d["date"] >= start).astype(int)
    for i, c in enumerate(controls):
        d[f"c{i}"] = (d["date"] >= c).astype(int)
        terms.append(f"c{i}")
    m = smf.ols("ci ~ " + " + ".join(terms) + " + C(moy)", data=d).fit()
    return m.params["post_x"]


def main():
    ci = _prep(pd.read_csv(DATA / "processed" / "certainty_index_main.csv"))
    real = {"GB": "2026-03-01", "AE": "2026-03-01"}
    rows, draws = [], []
    for c, real_date in real.items():
        d = ci[ci["country"] == c].sort_values("date").reset_index(drop=True)
        # observe only up to 2025-02 for placebos so the real shock is never in the sample
        pre = d[d["date"] < "2025-03-01"].reset_index(drop=True)
        covid = [pd.Timestamp("2020-03-01")]
        placebo = [level_jump(pre, pd.Timestamp(m), covid)
                   for m in pd.date_range("2021-01-01", "2024-09-01", freq="MS")]
        actual = level_jump(d, pd.Timestamp(real_date), covid)
        draws += [{"country": c, "jump": j} for j in placebo]
        p = np.mean(np.abs(placebo) >= abs(actual))
        rows.append({"country": c, "real_jump_mar2026": round(actual, 3),
                     "placebo_mean": round(np.mean(placebo), 3), "placebo_sd": round(np.std(placebo), 3),
                     "placebo_max_abs": round(np.max(np.abs(placebo)), 3), "n_placebos": len(placebo),
                     "share_placebos_as_big": round(p, 3)})
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUTS / "tables" / "placebo.csv", index=False)
    pd.DataFrame(draws).to_csv(OUTPUTS / "tables" / "placebo_draws.csv", index=False)
    print(out.to_string(index=False))

    # extended check: every month Sep 2020 - Aug 2025, sample ending Feb 2026 (before the real shock)
    d = ci[ci["country"] == "GB"].sort_values("date").reset_index(drop=True)
    pre = d[d["date"] < "2026-03-01"].reset_index(drop=True)
    months = pd.date_range("2020-09-01", "2025-08-01", freq="MS")
    ext = pd.DataFrame({"month": months.date, "jump": [level_jump(pre, m, [pd.Timestamp("2020-03-01")]) for m in months]})
    ext.to_csv(OUTPUTS / "tables" / "placebo_extended.csv", index=False)
    print(f"extended GB placebo: {len(ext)} months, largest jump {ext['jump'].max():.3f}")


if __name__ == "__main__":
    main()
