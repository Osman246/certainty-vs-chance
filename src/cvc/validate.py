"""Step 4: check Claude's homework.

1. Agreement with your hand labels (data/labels/human.csv: id, reward_type, stance, money_pressure)
   -> Cohen's kappa + macro F1 per field.
2. Test-retest: run 1 vs run 2 -> kappa (should be very high at temperature 0).

Rule of thumb for kappa: >0.8 strong, 0.6-0.8 substantial, <0.6 revisit the codebook.
"""
from __future__ import annotations

import pandas as pd
from sklearn.metrics import classification_report, cohen_kappa_score, f1_score

from . import DATA, OUTPUTS, load_yaml


def compare(a: pd.DataFrame, b: pd.DataFrame, fields: list[str], name: str) -> pd.DataFrame:
    m = a.merge(b, on="id", suffixes=("_a", "_b"))
    rows = []
    for f in fields:
        x, y = m[f"{f}_a"].astype(str), m[f"{f}_b"].astype(str)
        rows.append({
            "comparison": name, "field": f, "n": len(m),
            "kappa": round(cohen_kappa_score(x, y), 3),
            "macro_f1": round(f1_score(x, y, average="macro"), 3),
            "raw_agreement": round((x == y).mean(), 3),
        })
    return pd.DataFrame(rows)


def main():
    fields = list(load_yaml("codebook.yaml")["fields"].keys())
    lab = DATA / "labels"
    run1 = pd.read_csv(lab / "claude_run1.csv")
    results = []
    if (lab / "human.csv").exists():
        human = pd.read_csv(lab / "human.csv")
        results.append(compare(human, run1, fields, "human_vs_claude"))
        m = human.merge(run1, on="id", suffixes=("_human", "_claude"))
        print(classification_report(m["reward_type_human"].astype(str), m["reward_type_claude"].astype(str), zero_division=0))
    else:
        print("No data/labels/human.csv yet: hand-label a random sample (see docs/labelling_guide.md).")
    if (lab / "claude_run2.csv").exists():
        results.append(compare(run1, pd.read_csv(lab / "claude_run2.csv"), fields, "claude_run1_vs_run2"))
    if results:
        df = pd.concat(results, ignore_index=True)
        df.to_csv(OUTPUTS / "tables" / "validation.csv", index=False)
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()
