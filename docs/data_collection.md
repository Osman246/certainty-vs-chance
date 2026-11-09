# How the data was collected (8 November 2026)

## 1. Monthly search interest: `data/raw/trends_long.csv`
- Source: Google Trends, the same endpoint the trends.google.com Explore page uses, called from a logged-in browser session.
- 32 terms (17 UK, 15 UAE) from `config/terms.yaml`, **each requested on its own** (`geo=GB` or `geo=AE`, `2019-01-01 2026-10-31`, all categories, web search).
- Monthly values, 0–100 on each term's own scale. 94 months per term.
- Why one term per request: Google scales a multi-term request to its largest term and rounds to whole numbers, so small terms ("prize draw", "instant win") show as 0 next to "discount code".

`python -m cvc.collect_trends` (pytrends) does the same from a script, but Google rate-limits it heavily.

## 2. Related queries: `data/raw/related_rows_compact.txt`
- Source: the "Related queries → Top" list from Google Trends.
- Seeds: UK `deals, offer, competition, giveaway`; UAE `offers, عروض, raffle, win`. Also collected but not used in v1: UK `win, cashback, voucher, free gift`; UAE `giveaway, cashback, discount, خصم, سحب`.
- Window: 1 Aug – 30 Nov for each year 2019–2025, and 1 Aug – 7 Nov 2026.
- Up to 25 top queries per seed-year, with Google's relative value (0–100). 1,518 rows, 669 unique queries. UAE "win" 2025 returned no list.
- Format: `CCyyS=qid,value;...` where CC = country, yy = year, S = seed index (order above), and qid refers to `data/labels/query_labels_claude_compact.txt`.

## 3. Labels: `data/labels/query_labels_claude_compact.txt`
- Every unique query was labelled by Claude (Opus 5.5) against `config/codebook_queries.yaml` v1.0. Coding decisions are noted in the file header.
- To re-label through the API with the same codebook: `python -m cvc.label_queries --label`.

## Sources tried and not used
- **Reddit:** blocked for automated browser access, and not routed around. `src/cvc/collect_posts.py` uses the official API if you have keys.
- **MoneySavingExpert forums:** reachable but UK-only, so not comparable between countries in v1.
