"""Generate SYNTHETIC data so the whole pipeline can be tested before real collection.

Everything this writes is fake, with effects planted on purpose. It drops a DEMO_DATA marker
so every chart is stamped "DEMO DATA - NOT REAL RESULTS". Never publish these numbers.
Delete data/raw/* before running the real collection.
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
rng = np.random.default_rng(7)
dates = pd.date_range("2019-01-01", "2026-10-01", freq="MS")


def series(base, shocks):
    t = np.arange(len(dates))
    season = 8 * np.sin(2 * np.pi * (dates.month - 3) / 12)
    y = base + season + rng.normal(0, 3, len(dates))
    for start, jump in shocks:
        y = y + jump * (dates >= pd.Timestamp(start))
    return np.clip(y, 1, 100)


rows = []
plan = {
    "GB": {"certainty": (40, [("2022-04-01", 12)]), "chance": (45, [("2020-03-01", 6), ("2022-04-01", -6)])},
    "AE": {"certainty": (35, [("2026-03-01", 15), ("2026-06-01", -8)]), "chance": (50, [("2026-03-01", -12), ("2026-06-01", 6)])},
}
for c, sides in plan.items():
    for side, (base, sh) in sides.items():
        for k in range(3):
            y = series(base + rng.normal(0, 4), sh)
            rows += [{"date": d, "term": f"{side}_term_{k}", "interest": v, "country": c, "side": side,
                      "circle": "inner" if side == "chance" else "industry"} for d, v in zip(dates, y)]
df = pd.DataFrame(rows)
for c in plan:
    df[df.country == c].to_csv(RAW / f"trends_{c}.csv", index=False)

templates = {
    "chance": ["entered the {b} win a holiday comp, fingers crossed", "these mall raffles are a scam, never win",
               "won a prize draw for the first time!! love it", "is the {b} instant win still running?"],
    "cash_saving": ["with bills this high I only use cashback now", "great voucher code for {b}, saved 20%",
                    "discount code worked, worth it", "cutting back so only buying on sale"],
    "loyalty": ["{b} points going further this month", "clubcard prices saved me loads, recommend"],
    "free_gift": ["free gift with the {b} set is great", "anyone know if the free tote is still on?"],
    "credit": ["paid with tabby in 4 because salary is late", "klarna for the school shoes, tight month"],
}
brands = ["Walkers", "Boots", "Carrefour", "Noon", "Tesco", "Lulu"]
posts = []
for i in range(1200):
    d = dates[rng.integers(0, len(dates))]
    c = rng.choice(["GB", "AE"])
    p_chance = 0.4 - 0.15 * (c == "GB" and d >= pd.Timestamp("2022-04-01")) - 0.2 * (c == "AE" and pd.Timestamp("2026-03-01") <= d < pd.Timestamp("2026-06-01"))
    rt = "chance" if rng.random() < p_chance else rng.choice(["cash_saving", "loyalty", "free_gift", "credit"], p=[.5, .2, .2, .1])
    text = rng.choice(templates[rt]).format(b=rng.choice(brands))
    posts.append({"id": i, "date": (d + pd.Timedelta(days=int(rng.integers(0, 27)))).date(), "country": c, "source": "synthetic", "text": text})
pd.DataFrame(posts).to_csv(RAW / "posts.csv", index=False)
(RAW / "DEMO_DATA").write_text("Synthetic data. Delete data/raw/* before real collection.\n")
print("Synthetic demo data written to data/raw/ (marked DEMO_DATA).")
