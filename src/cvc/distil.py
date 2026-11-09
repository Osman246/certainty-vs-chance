"""Step 6 (supervised): distil Claude into a small, cheap classifier.

Train logistic regression on Claude's reward_type labels (the "teacher"), then measure:
  - how well the student agrees with Claude on held-out posts
  - how well both agree with YOUR hand labels (the real ground truth), if available
Features: multilingual sentence embeddings if sentence-transformers is installed, else TF-IDF.

Why it matters: once trained, the student labels millions of posts for ~free and gives
identical answers every time, which makes the study cheap and reproducible.
"""
from __future__ import annotations

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import cohen_kappa_score, f1_score
from sklearn.model_selection import train_test_split

from . import DATA, OUTPUTS


def featurise(texts: list[str]):
    try:
        from sentence_transformers import SentenceTransformer

        m = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        return m.encode(texts, show_progress_bar=False), "multilingual-MiniLM embeddings"
    except ImportError:
        from sklearn.feature_extraction.text import TfidfVectorizer

        return TfidfVectorizer(ngram_range=(1, 2), min_df=2).fit_transform(texts), "TF-IDF (fallback)"


def main(field: str = "reward_type"):
    posts = pd.read_csv(DATA / "raw" / "posts.csv")
    teacher = pd.read_csv(DATA / "labels" / "claude_run1.csv")[["id", field]]
    df = posts.merge(teacher, on="id").dropna(subset=[field]).reset_index(drop=True)
    X, feat_name = featurise(df["text"].astype(str).tolist())
    y = df[field].astype(str)

    idx_tr, idx_te = train_test_split(df.index, test_size=0.25, random_state=42, stratify=y)
    clf = LogisticRegression(max_iter=2000, class_weight="balanced")
    clf.fit(X[idx_tr], y[idx_tr])
    pred = pd.Series(clf.predict(X[idx_te]), index=idx_te)

    rows = [{
        "comparison": "student_vs_claude (held-out)", "features": feat_name, "n": len(idx_te),
        "kappa": round(cohen_kappa_score(y[idx_te], pred), 3),
        "macro_f1": round(f1_score(y[idx_te], pred, average="macro"), 3),
    }]

    human_path = DATA / "labels" / "human.csv"
    if human_path.exists():
        human = pd.read_csv(human_path)[["id", field]].rename(columns={field: "human"})
        te = df.loc[idx_te, ["id"]].assign(student=pred.values, claude=y[idx_te].values).merge(human, on="id")
        for who in ["student", "claude"]:
            if len(te):
                rows.append({
                    "comparison": f"{who}_vs_human", "features": feat_name, "n": len(te),
                    "kappa": round(cohen_kappa_score(te["human"], te[who]), 3),
                    "macro_f1": round(f1_score(te["human"], te[who], average="macro"), 3),
                })
    res = pd.DataFrame(rows)
    res.to_csv(OUTPUTS / "tables" / "distillation.csv", index=False)
    print(res.to_string(index=False))


if __name__ == "__main__":
    main()
