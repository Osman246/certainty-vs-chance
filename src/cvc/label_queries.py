"""Step 3 (text layer): classify Google Trends related queries with Claude, then summarise.

Inputs:  data/raw/related_queries.csv   (country, year, seed, kind[top|rising], query, value)
Labels:  data/labels/query_labels_claude.csv  (query, reward_type, object, money_pressure)
         produced either by:
           python -m cvc.label_queries --label           # Claude API (needs ANTHROPIC_API_KEY)
         or supplied (this study's run was labelled by Claude Opus 5.5 in-session, same codebook).
Checks:  agreement with an independent keyword-rule coder (a different method, not a gold standard).
Outputs: data/processed/query_shares.csv, outputs/tables/query_*.csv
"""
from __future__ import annotations

import argparse
import json
import re

import pandas as pd
from sklearn.metrics import cohen_kappa_score

from . import DATA, OUTPUTS, load_yaml

NEUTRAL = {"GB": {"deals", "offer"}, "AE": {"offers", "عروض"}}
CERTAINTY = {"cash_saving", "free_gift", "loyalty"}


def rule_reward(q: str) -> str:
    q = q.lower()
    if re.search(r"\b(win|winner|competition|comp|prize|raffle|draw|giveaway|sweepstake|lottery|lotto)\b|سحب|مسابق|اربح|جائز", q):
        return "chance"
    if re.search(r"\b(klarna|clearpay|tabby|tamara|pay later|instal)", q):
        return "credit"
    if re.search(r"\b(points|clubcard|nectar|loyalty|rewards card|share)\b", q):
        return "loyalty"
    if re.search(r"\b(free gift|freebie|gift with|sample)\b", q):
        return "free_gift"
    if re.search(r"\b(cashback|cash back|discount|voucher|code|coupon|sale|deal|deals|offer|offers|promo|% off)\b|خصم|كوبون|عروض|تخفيض", q):
        return "cash_saving"
    return "none"


def label_api(queries: list[str], model: str) -> pd.DataFrame:
    """Claude API path: few-shot, temperature 0, forced tool output (same method as label_llm)."""
    import anthropic

    cb = load_yaml("codebook_queries.yaml")
    client = anthropic.Anthropic()
    props = {f: {"type": "string", "enum": list(s["labels"].keys())} for f, s in cb["fields"].items()}
    tool = {"name": "record", "description": "Labels for one search query",
            "input_schema": {"type": "object", "properties": props, "required": list(props)}}
    system = "Classify Google search queries with this codebook. Use only these labels.\n" + json.dumps(
        {f: s["labels"] for f, s in cb["fields"].items()}, ensure_ascii=False) + "\nExamples:\n" + "\n".join(
        json.dumps(e, ensure_ascii=False) for e in cb["examples"])
    rows = []
    for q in queries:
        m = client.messages.create(model=model, max_tokens=150, temperature=0, system=system, tools=[tool],
                                   tool_choice={"type": "tool", "name": "record"},
                                   messages=[{"role": "user", "content": q}])
        rows.append({"query": q, **next(b for b in m.content if b.type == "tool_use").input})
    return pd.DataFrame(rows)


def summarise():
    rq = pd.read_csv(DATA / "raw" / "related_queries.csv")
    lab = pd.read_csv(DATA / "labels" / "query_labels_claude.csv")
    df = rq.merge(lab, on="query", how="left")
    assert df["reward_type"].notna().all(), "unlabelled queries"
    t = OUTPUTS / "tables"

    # 1. method check: Claude vs independent keyword rules
    u = lab.assign(rule=lab["query"].map(rule_reward))
    k, agree = cohen_kappa_score(u["reward_type"], u["rule"]), (u["reward_type"] == u["rule"]).mean()
    pd.DataFrame([{"comparison": "claude_vs_keyword_rules", "field": "reward_type", "n_unique_queries": len(u),
                   "kappa": round(k, 3), "raw_agreement": round(agree, 3)}]).to_csv(t / "query_label_agreement.csv", index=False)

    def share(d, col):
        w = d.groupby(["country", "year", col])["value"].sum().unstack(col, fill_value=0)
        return (w.div(w.sum(axis=1), axis=0) * 100).round(1)

    # 2. what people try to SAVE on: neutral seeds, guaranteed-reward queries, weighted by Google's relative value
    neu = df[[s in NEUTRAL[c] for c, s in zip(df["country"], df["seed"])]]
    sav = share(neu[neu["reward_type"].isin(CERTAINTY)], "object")
    sav.to_csv(t / "query_savings_objects.csv")

    # 3. what people try to WIN: prize seeds, chance queries
    prize = df[~df.index.isin(neu.index)]
    win = share(prize[prize["reward_type"] == "chance"], "object")
    win.to_csv(t / "query_prize_objects.csv")

    # 4. how much of a prize-seed search is actually a consumer prize promotion (vs elections, sport, BMW models)
    sig = prize.assign(p=(prize["reward_type"] == "chance") * prize["value"]).groupby(["country", "year"]).apply(
        lambda g: round(100 * g["p"].sum() / g["value"].sum(), 1), include_groups=False).rename("prize_promo_share")
    sig.reset_index().to_csv(t / "query_prize_signal_share.csv", index=False)

    keyshares = pd.DataFrame({
        "savings_groceries_pct": sav.get("groceries"), "savings_cash_bank_pct": sav.get("cash"),
        "prize_car_pct": win.get("car"), "prize_cash_pct": win.get("cash")}).reset_index()
    keyshares.to_csv(DATA / "processed" / "query_shares.csv", index=False)
    print(f"Claude vs keyword rules: kappa={k:.3f}, agreement={agree:.1%}")
    print(keyshares.to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", action="store_true", help="label with the Claude API")
    ap.add_argument("--model", default="claude-sonnet-5-5")
    a = ap.parse_args()
    if a.label:
        rq = pd.read_csv(DATA / "raw" / "related_queries.csv")
        from .parse_related import M, O, R
        inv = lambda d: {v: k for k, v in d.items()}
        lab = pd.read_csv(DATA / "labels" / "query_labels_claude.csv")          # keeps the original query ids
        new = label_api(lab["query"].tolist(), a.model)
        path = DATA / "labels" / "query_labels_claude_compact.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# Labelled by {a.model} via the API against config/codebook_queries.yaml\n")
            for i, r in new.iterrows():
                f.write(f"{i}|{inv(R)[r.reward_type]}{inv(O)[r.object]}{inv(M)[r.money_pressure]}|{r.query}\n")
        print(f"wrote {path}; now run: python run_pipeline.py")
        return
    summarise()


if __name__ == "__main__":
    main()
