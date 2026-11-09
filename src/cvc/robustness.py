"""Robustness: does the March 2026 UK jump survive dropping the terms most open to supply-side effects?

Re-estimates the ITS level jump at each shock after removing:
  - cashback        (banks pushed cashback cards/current accounts in 2026)
  - win a / win     (generic 'win' searches are mostly elections and sport)
  - both
  - prize-competition platforms can't be removed term-by-term, so 'giveaway' and 'competitions' are dropped together
"""
import re

import pandas as pd

from . import DATA, OUTPUTS, load_yaml
from .index import certainty_index
from .regress import _prep, its

SPECS = {
    "main": (),
    "no_cashback": ("cashback",),
    "no_generic_win": ("win a", "win"),
    "no_cashback_no_win": ("cashback", "win a", "win"),
    "no_comp_platform_terms": ("giveaway", "competitions"),
    "english_only": "ARABIC",
    "no_voucher_code": ("voucher code",),   # wording shift: "voucher code" -> "discount code"
    "no_codes": ("voucher code", "discount code"),
}


def main():
    shocks = load_yaml("shocks.yaml")
    rel = pd.read_csv(DATA / "processed" / "trends_relative.csv", parse_dates=["date"])
    arabic = rel["term"].map(lambda t: bool(re.search("[؀-ۿ]", t)))
    out = []
    for name, drop in SPECS.items():
        ci = certainty_index(rel[~arabic]) if drop == "ARABIC" else certainty_index(rel, drop_terms=drop)
        r = its(_prep(ci), shocks, name)
        out.append(r[r["term"].isin(["hormuz_energy", "iran_war", "ceasefire", "covid_lockdown"])])
    df = pd.concat(out)
    df.to_csv(OUTPUTS / "tables" / "robustness.csv", index=False)
    piv = df[df["effect"] == "level jump"].pivot_table(index=["country", "term"], columns="variant", values="coef").round(2)
    pv = df[df["effect"] == "level jump"].pivot_table(index=["country", "term"], columns="variant", values="p").round(3)
    pd.set_option("display.width", 220)
    print("level jump coefficients\n", piv.to_string(), "\n\np-values\n", pv.to_string())


if __name__ == "__main__":
    main()
