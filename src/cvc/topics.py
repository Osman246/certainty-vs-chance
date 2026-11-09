"""Step 5 (unsupervised): let the data show its own themes before we impose the codebook.

Primary: BERTopic (sentence embeddings -> UMAP -> HDBSCAN -> c-TF-IDF topic words).
Fallback (no heavy installs): TF-IDF + NMF, so the step still runs anywhere.

    python -m cvc.topics             # BERTopic if installed, else NMF
    python -m cvc.topics --nmf       # force the lightweight fallback
"""
from __future__ import annotations

import argparse

import pandas as pd

from . import DATA, OUTPUTS


def run_bertopic(texts: list[str]) -> pd.DataFrame:
    from bertopic import BERTopic
    from sentence_transformers import SentenceTransformer

    emb_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")  # handles English + Arabic
    model = BERTopic(embedding_model=emb_model, min_topic_size=15, verbose=True)
    topics, _ = model.fit_transform(texts)
    info = model.get_topic_info()
    info.to_csv(OUTPUTS / "tables" / "topics_bertopic.csv", index=False)
    return pd.DataFrame({"topic": topics})


def run_nmf(texts: list[str], k: int = 8) -> pd.DataFrame:
    from sklearn.decomposition import NMF
    from sklearn.feature_extraction.text import TfidfVectorizer

    vec = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), min_df=2, stop_words="english")
    X = vec.fit_transform(texts)
    nmf = NMF(n_components=k, random_state=42, init="nndsvda", max_iter=500)
    W = nmf.fit_transform(X)
    words = vec.get_feature_names_out()
    rows = [{"topic": i, "top_words": ", ".join(words[j] for j in comp.argsort()[-8:][::-1])}
            for i, comp in enumerate(nmf.components_)]
    pd.DataFrame(rows).to_csv(OUTPUTS / "tables" / "topics_nmf.csv", index=False)
    for r in rows:
        print(f"  topic {r['topic']}: {r['top_words']}")
    return pd.DataFrame({"topic": W.argmax(axis=1)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nmf", action="store_true")
    args = ap.parse_args()
    posts = pd.read_csv(DATA / "raw" / "posts.csv")
    texts = posts["text"].astype(str).tolist()
    if args.nmf:
        t = run_nmf(texts)
    else:
        try:
            t = run_bertopic(texts)
        except ImportError:
            print("BERTopic not installed; using TF-IDF + NMF fallback.")
            t = run_nmf(texts)
    pd.concat([posts[["id", "date", "country"]], t], axis=1).to_csv(DATA / "processed" / "post_topics.csv", index=False)


if __name__ == "__main__":
    main()
