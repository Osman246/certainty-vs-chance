"""The ML layer, on the real Claude-labelled search queries.

1. Unsupervised: cluster the queries with no labels (character n-gram TF-IDF -> NMF topics), then ask:
   do the clusters line up with Claude's codebook? (Adjusted Rand Index, cluster purity)
2. Supervised: train a cheap classifier (logistic regression on character n-grams) to reproduce
   Claude's reward_type labels; 5-fold cross-validated accuracy, macro-F1 and Cohen's kappa.
   Compared against the hand-written keyword rules as a baseline.

Character n-grams are used because queries are 1-6 words and mix English and Arabic.
"""
import numpy as np
import pandas as pd
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import adjusted_rand_score, cohen_kappa_score, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline

from . import DATA, OUTPUTS
from .label_queries import rule_reward


def main():
    lab = pd.read_csv(DATA / "labels" / "query_labels_claude.csv")
    X_text, y = lab["query"].astype(str), lab["reward_type"]
    t = OUTPUTS / "tables"

    # 1. unsupervised
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)
    X = vec.fit_transform(X_text)
    k = 8
    W = NMF(n_components=k, random_state=42, init="nndsvda", max_iter=800).fit_transform(X)
    cl = W.argmax(1)
    lab["cluster"] = cl
    ari = adjusted_rand_score(y, cl)
    purity = lab.groupby("cluster")["reward_type"].agg(lambda s: s.value_counts(normalize=True).iloc[0])
    summ = lab.groupby("cluster").agg(n=("query", "size"), top_label=("reward_type", lambda s: s.value_counts().index[0]),
                                      examples=("query", lambda s: " | ".join(s.head(5))))
    summ["purity"] = purity.round(2)
    summ.to_csv(t / "ml_unsupervised_clusters.csv")

    # 2. supervised distillation
    clf = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True),
                        LogisticRegression(max_iter=3000, class_weight="balanced", C=5))
    keep = y.map(y.value_counts()) >= 5          # classes with too few examples can't be cross-validated
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    pred = cross_val_predict(clf, X_text[keep], y[keep], cv=cv)
    rules = X_text.map(rule_reward)
    res = pd.DataFrame([
        {"model": "logistic regression (char n-grams), 5-fold CV", "n": int(keep.sum()),
         "accuracy": (pred == y[keep]).mean(), "macro_f1": f1_score(y[keep], pred, average="macro"),
         "kappa_vs_claude": cohen_kappa_score(y[keep], pred)},
        {"model": "keyword rules (no learning)", "n": len(y),
         "accuracy": (rules == y).mean(), "macro_f1": f1_score(y, rules, average="macro"),
         "kappa_vs_claude": cohen_kappa_score(y, rules)},
        {"model": "unsupervised NMF clusters (k=8) vs Claude labels", "n": len(y),
         "accuracy": np.nan, "macro_f1": np.nan, "kappa_vs_claude": np.nan, "adjusted_rand_index": ari,
         "mean_cluster_purity": purity.mean()},
    ]).round(3)
    res.to_csv(t / "ml_results.csv", index=False)
    lab.loc[keep].assign(student=pred).query("student != reward_type")[["query", "reward_type", "student"]].to_csv(
        t / "ml_student_disagreements.csv", index=False)
    pd.set_option("display.width", 200, "display.max_colwidth", 70)
    print(res.to_string(index=False))
    print(summ.to_string())


if __name__ == "__main__":
    main()
