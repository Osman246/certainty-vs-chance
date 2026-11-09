"""Charts sized for LinkedIn (1080x1350 portrait) and the README.

1. 01_certainty_index.png - UK vs UAE Certainty Index 2019-2026, shocks marked (hero)
2. 02_same_season.png     - Aug-Oct average by year (year-on-year, how the business reads it)
3. 03_what_moved.png      - every term: change from 2019 to 2026 (Aug-Oct)
4. 04_placebo.png         - is the 2026 UK jump real? placebo distribution vs actual
5. 05_query_mix.png       - Claude-labelled related searches: chance vs guaranteed share by year
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import DATA, OUTPUTS, load_yaml

COL = {"GB": "#1f4e8c", "AE": "#8a8173", "chance": "#c48216", "certainty": "#106270"}  # ochre = chance, teal = certainty (as in the video)
NAME = {"GB": "UK", "AE": "UAE"}
GLOSS = {"سحب": "draw (AR)", "مسابقة": "competition (AR)", "خصم": "discount (AR)", "عروض": "offers (AR)",
         "كوبون": "coupon (AR)", "اربح": "win (AR)"}
INK, MUTED = "#1d1d1f", "#6e6e73"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 15, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.2,
                     "axes.edgecolor": MUTED, "text.color": INK, "axes.labelcolor": INK})
SRC = "Data: Google Trends (UK & UAE, monthly, 2019-2026). Analysis: Sahil Osman."


def _save(fig, name):
    fig.text(0.02, 0.012, SRC, fontsize=10, color=MUTED)
    fig.savefig(OUTPUTS / "charts" / name, dpi=100, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _title(ax, title, sub):
    ax.set_title(title, loc="left", fontsize=26, fontweight="bold", pad=48)
    ax.text(0, 1.035, sub, transform=ax.transAxes, fontsize=14, color=MUTED, va="bottom")


def hero(ci: pd.DataFrame, shocks: dict):
    fig, ax = plt.subplots(figsize=(10.8, 13.5))
    for c in ["GB", "AE"]:
        g = ci[ci["country"] == c].set_index("date")["ci"].rolling(3, min_periods=1).mean()
        ax.plot(g.index, g.values, lw=3.5, color=COL[c], label=NAME[c])
        ax.text(g.index[-1] + pd.Timedelta(days=20), g.values[-1], NAME[c], color=COL[c], fontsize=16, fontweight="bold", va="center")
    marks = [("2020-03-01", "COVID\nlockdown"), ("2022-04-01", "UK energy\ncap rise"), ("2026-03-01", "Iran war /\nHormuz")]
    ymin, ymax = ax.get_ylim()
    for d, lab in marks:
        x = pd.Timestamp(d)
        ax.axvline(x, color=MUTED, ls=":", lw=1.3)
        ax.text(x + pd.Timedelta(days=25), ymin + 0.02 * (ymax - ymin), lab, fontsize=12, color=MUTED, va="bottom")
    ax.axhline(0, color=INK, lw=0.8)
    ax.text(pd.Timestamp("2023-03-01"), 0.015, "2019 balance", fontsize=11, color=MUTED, va="bottom")
    ax.set_ylabel("← chasing prizes          chasing guaranteed rewards →", fontsize=14)
    _title(ax, "Win it, or be sure of it?", "Certainty Index: guaranteed-reward searches vs prize searches, vs 2019 (3-month avg)")
    _save(fig, "01_certainty_index.png")


def same_season(tbl: pd.DataFrame):
    p = tbl.pivot(index="year", columns="country", values="ci")[["GB", "AE"]]
    fig, ax = plt.subplots(figsize=(10.8, 13.5))
    x = np.arange(len(p))
    for i, c in enumerate(["GB", "AE"]):
        bars = ax.bar(x + (i - 0.5) * 0.38, p[c], 0.38, color=COL[c], label=NAME[c])
        for b, v in zip(bars, p[c]):
            if abs(v) < 0.12:
                continue
            ax.text(b.get_x() + b.get_width() / 2, v + (0.02 if v >= 0 else -0.02), f"{v:+.2f}",
                    ha="center", va="bottom" if v >= 0 else "top", fontsize=11, color=COL[c])
    ax.set_xticks(x, p.index)
    ax.axhline(0, color=INK, lw=0.8)
    ax.legend(frameon=False, loc="upper left", fontsize=15)
    ax.set_ylabel("← prizes          guaranteed rewards →", fontsize=14)
    _title(ax, "Same season, every year", "Aug-Oct average Certainty Index, 2019-2026")
    _save(fig, "02_same_season.png")


def what_moved(rel: pd.DataFrame):
    """Before the shock: full-year 2025 vs 2019, per term. 'voucher code' is left out because its fall is a
    wording change ("discount code" replaced it), not a change in what people wanted."""
    s = rel[rel["side"].isin(["chance", "certainty"]) & rel["date"].dt.year.isin([2019, 2025]) & (rel["term"] != "voucher code")]
    t = s.groupby(["country", "term", "side", s["date"].dt.year])["interest"].mean().unstack()
    t["pct"] = (t[2025] + 1) / (t[2019] + 1) * 100 - 100
    t = t.reset_index()
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 13.5))
    for ax, c in zip(axes, ["GB", "AE"]):
        d = t[t["country"] == c].sort_values("pct")
        ax.barh(d["term"].map(lambda x: GLOSS.get(x, x)), d["pct"], color=[COL[x] for x in d["side"]])
        for y, v in enumerate(d["pct"]):
            ax.text(v + (4 if v >= 0 else -4), y, f"{v:+.0f}%", va="center", ha="left" if v >= 0 else "right", fontsize=11)
        ax.axvline(0, color=INK, lw=0.8)
        ax.set_title(NAME[c], fontsize=20, fontweight="bold", color=COL[c], loc="left")
        lim = max(abs(d["pct"].min()), d["pct"].max()) * 1.35
        ax.set_xlim(-lim, lim)
        ax.grid(axis="y", visible=False)
    fig.suptitle("Before the shock: 2025 vs 2019 (full-year averages)", x=0.02, ha="left", fontsize=24, fontweight="bold", y=1.0)
    fig.text(0.02, 0.955, "\u25a0 prize searches     ", color=COL["chance"], fontsize=15)
    fig.text(0.30, 0.955, "\u25a0 guaranteed-reward searches", color=COL["certainty"], fontsize=15)
    fig.text(0.02, 0.035, "\"voucher code\" left out: it was replaced by \"discount code\" (a wording change).", fontsize=11, color=MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    _save(fig, "03_what_moved.png")


def placebo_chart():
    p = OUTPUTS / "tables" / "placebo_draws.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    real = pd.read_csv(OUTPUTS / "tables" / "placebo.csv").set_index("country")
    fig, axes = plt.subplots(2, 1, figsize=(10.8, 13.5))
    for ax, c in zip(axes, ["GB", "AE"]):
        ax.hist(d[d["country"] == c]["jump"], bins=15, color="#c7c7cc")
        r = real.loc[c, "real_jump_mar2026"]
        ax.axvline(r, color=COL[c], lw=4)
        ax.text(r, ax.get_ylim()[1] * 0.92, f"  March 2026\n  {r:+.2f}", color=COL[c], fontsize=14, fontweight="bold", va="top")
        ax.set_title(f"{NAME[c]}: {int(real.loc[c,'n_placebos'])} fake shocks (grey) vs the real one", loc="left", fontsize=17)
        ax.set_xlabel("Jump in Certainty Index")
    fig.suptitle("Is the 2026 shift real, or just noise?", x=0.02, ha="left", fontsize=26, fontweight="bold")
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    _save(fig, "04_placebo.png")


def query_mix():
    p = DATA / "processed" / "query_shares.csv"
    if not p.exists():
        return
    q = pd.read_csv(p)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10.8, 13.5))
    ae = q[q["country"] == "AE"]
    a1.plot(ae["year"], ae["savings_groceries_pct"], marker="o", lw=3.5, ms=9, color=COL["AE"], label="groceries & supermarkets")
    a1.plot(ae["year"], ae["savings_cash_bank_pct"], marker="s", lw=3.5, ms=9, color=COL["certainty"], label="bank & credit-card offers")
    a1.set_title("UAE: what people search 'offers' for", loc="left", fontsize=19, fontweight="bold")
    a1.set_ylabel("% of savings searches")
    a1.legend(frameon=False, fontsize=13)
    gb = q[q["country"] == "GB"]
    a2.plot(gb["year"], gb["prize_car_pct"], marker="o", lw=3.5, ms=9, color=COL["GB"])
    a2.set_title("UK: share of prize searches that are about winning a car", loc="left", fontsize=19, fontweight="bold")
    a2.set_ylabel("% of prize searches")
    a2.set_ylim(0, 30)
    a1.set_ylim(0, 50)
    for a in (a1, a2):
        a.set_xticks(range(2019, 2027))
    fig.suptitle("What people actually typed", x=0.02, ha="left", fontsize=26, fontweight="bold")
    fig.text(0.02, 0.945, "Google related searches, Aug-Nov each year, classified by Claude", fontsize=14, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 0.94))
    _save(fig, "05_what_people_typed.png")


def main():
    shocks = load_yaml("shocks.yaml")
    ci = pd.read_csv(DATA / "processed" / "certainty_index_main.csv", parse_dates=["date"])
    rel = pd.read_csv(DATA / "processed" / "trends_relative.csv", parse_dates=["date"])
    hero(ci, shocks)
    same_season(pd.read_csv(OUTPUTS / "tables" / "seasonal_aug_oct.csv"))
    what_moved(rel)
    placebo_chart()
    query_mix()
    print("charts saved to outputs/charts/")


if __name__ == "__main__":
    main()
