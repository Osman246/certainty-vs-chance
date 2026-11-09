"""Turn the compact browser exports into tidy CSVs.

data/raw/related_rows_compact.txt   key=qid,value;...   key = CC + yy + seed index
data/labels/query_labels_claude_compact.txt   id|code|query   (Claude Opus 5.5 labels)
"""
import pandas as pd

from . import DATA

SEEDS = {"GB": ["deals", "offer", "competition", "giveaway"], "AE": ["offers", "عروض", "raffle", "win"]}
R = {"c": "chance", "s": "cash_saving", "g": "free_gift", "l": "loyalty", "r": "credit", "n": "none"}
O = {"$": "cash", "t": "travel", "v": "car", "k": "tech", "f": "groceries", "b": "fashion_beauty",
     "h": "home", "o": "other", "-": "none"}
M = {"y": "yes", "n": "no"}


def main():
    lab = []
    for line in open(DATA / "labels" / "query_labels_claude_compact.txt", encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        i, code, q = line.rstrip("\n").split("|", 2)
        lab.append({"qid": int(i), "query": q, "reward_type": R[code[0]], "object": O[code[1]], "money_pressure": M[code[2]]})
    lab = pd.DataFrame(lab)
    assert lab["qid"].is_unique and len(lab) == lab["qid"].max() + 1
    rows = []
    for line in open(DATA / "raw" / "related_rows_compact.txt", encoding="utf-8"):
        key, vals = line.strip().split("=", 1)
        c, y, s = key[:2], 2000 + int(key[2:4]), int(key[4])
        for rank, pair in enumerate(vals.split(";"), 1):
            qid, v = pair.split(",")
            rows.append({"country": c, "year": y, "seed": SEEDS[c][s], "kind": "top", "rank": rank, "qid": int(qid), "value": int(v)})
    rows = pd.DataFrame(rows).merge(lab[["qid", "query"]], on="qid", how="left")
    assert rows["query"].notna().all()
    rows.to_csv(DATA / "raw" / "related_queries.csv", index=False)
    lab.drop(columns="qid").to_csv(DATA / "labels" / "query_labels_claude.csv", index=False)
    print(len(rows), "rows,", len(lab), "unique labelled queries")


if __name__ == "__main__":
    main()
