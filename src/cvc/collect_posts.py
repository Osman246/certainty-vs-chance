"""Step 1b: collect public posts for the LLM content analysis (Reddit official API via PRAW).

Setup (free): create a "script" app at https://www.reddit.com/prefs/apps, then
    export REDDIT_CLIENT_ID=... REDDIT_CLIENT_SECRET=... REDDIT_USER_AGENT="cvc-research by u/<you>"
    python -m cvc.collect_posts

Limits to state in the write-up: Reddit search returns at most ~250 results per query and
favours recent/popular posts, so older years are thinner. That's why the search index (Google Trends)
is the primary measure and posts are the triangulation layer.
Only post text, date and subreddit are kept: no usernames, nothing that identifies a person.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import pandas as pd

from . import DATA

SOURCES = {
    "GB": ["UKPersonalFinance", "CasualUK", "HotUKDeals", "unitedkingdom", "beermoneyuk"],
    "AE": ["dubai", "UAE", "abudhabi", "DubaiCentral"],
}
QUERIES = ["competition", "win", "prize draw", "raffle", "giveaway", "cashback",
           "discount code", "voucher", "loyalty points", "free gift", "buy now pay later", "tabby"]


def main(limit_per_query: int = 250):
    import praw

    r = praw.Reddit(client_id=os.environ["REDDIT_CLIENT_ID"], client_secret=os.environ["REDDIT_CLIENT_SECRET"],
                    user_agent=os.environ.get("REDDIT_USER_AGENT", "cvc-research"))
    rows, seen = [], set()
    for country, subs in SOURCES.items():
        for sub in subs:
            for q in QUERIES:
                try:
                    for s in r.subreddit(sub).search(q, sort="relevance", time_filter="all", limit=limit_per_query):
                        if s.id in seen:
                            continue
                        seen.add(s.id)
                        text = f"{s.title}. {s.selftext or ''}".strip()[:2000]
                        rows.append({"id": s.id, "date": datetime.fromtimestamp(s.created_utc, tz=timezone.utc).date(),
                                     "country": country, "source": f"r/{sub}", "query": q, "text": text})
                except Exception as e:
                    print(f"  skip r/{sub} '{q}': {e}")
            print(f"  r/{sub}: {len(rows)} posts so far")
    df = pd.DataFrame(rows)
    df = df[(df["date"] >= pd.Timestamp("2019-01-01").date())]
    df.to_csv(DATA / "raw" / "posts.csv", index=False)
    print(f"saved {len(df)} posts")
    print(df.groupby(["country", pd.to_datetime(df["date"]).dt.year]).size().unstack(0))


if __name__ == "__main__":
    main()
