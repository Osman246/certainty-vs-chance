"""Step 3: LLM-assisted content analysis. Claude does few-shot classification against the codebook.

Method: zero-temperature, few-shot classification against a fixed codebook, with output forced
through a tool schema so every answer is valid structured data (no free-text parsing).
Run it twice (`--run 1`, `--run 2`) to measure test-retest consistency in validate.py.

Input:  data/raw/posts.csv  with columns  id, date, country, source, text
Output: data/labels/claude_run<N>.csv

    export ANTHROPIC_API_KEY=...
    python -m cvc.label_llm --run 1
    python -m cvc.label_llm --run 1 --mock      # no API: keyword rules, for testing the pipeline only
"""
from __future__ import annotations

import argparse
import json
import re
import time

import pandas as pd

from . import DATA, load_yaml

DEFAULT_MODEL = "claude-sonnet-5-5"


def build_system_prompt(cb: dict) -> str:
    lines = [
        "You are a careful research assistant coding social media posts for a consumer-behaviour study.",
        "Apply the codebook exactly. If unsure, choose the closest label; never invent new labels.",
        "",
        "CODEBOOK",
    ]
    for field, spec in cb["fields"].items():
        lines.append(f"\n{field}: {spec['description']}")
        for lab, d in spec["labels"].items():
            lines.append(f"  - {lab}: {d}")
    lines.append("\nWORKED EXAMPLES")
    for ex in cb["examples"]:
        lab = {k: ex[k] for k in cb["fields"]}
        lines.append(f'Post: "{ex["text"]}"\nLabels: {json.dumps(lab)}')
    return "\n".join(lines)


def build_tool(cb: dict) -> dict:
    props = {f: {"type": "string", "enum": list(s["labels"].keys())} for f, s in cb["fields"].items()}
    props["evidence"] = {"type": "string", "description": "Up to 10 words from the post that justify reward_type."}
    return {
        "name": "record_labels",
        "description": "Record the codebook labels for one post.",
        "input_schema": {"type": "object", "properties": props, "required": list(props.keys())},
    }


def label_with_claude(texts: list[str], cb: dict, model: str) -> list[dict]:
    import anthropic

    client = anthropic.Anthropic()
    system = build_system_prompt(cb)
    tool = build_tool(cb)
    out = []
    for i, text in enumerate(texts):
        for attempt in range(4):
            try:
                msg = client.messages.create(
                    model=model,
                    max_tokens=300,
                    temperature=0,
                    system=system,
                    tools=[tool],
                    tool_choice={"type": "tool", "name": "record_labels"},
                    messages=[{"role": "user", "content": f'Post: "{text}"'}],
                )
                block = next(b for b in msg.content if b.type == "tool_use")
                out.append(dict(block.input))
                break
            except Exception as e:  # rate limits, transient errors
                wait = 2 ** attempt * 5
                print(f"  retry {attempt + 1} in {wait}s: {e}")
                time.sleep(wait)
        else:
            out.append({f: None for f in cb["fields"]} | {"evidence": "ERROR"})
        if (i + 1) % 50 == 0:
            print(f"  labelled {i + 1}/{len(texts)}")
    return out


# --- mock labeller: transparent keyword rules, ONLY for testing the pipeline without an API key ---
_RULES = [
    ("chance", r"\b(win|won|comp|competition|prize|raffle|draw|giveaway|sweep|instant win)\b|سحب|اربح"),
    ("credit", r"\b(klarna|clearpay|tabby|tamara|bnpl|pay later|instal)"),
    ("loyalty", r"\b(points|clubcard|nectar|loyalty|member price|share points|stamps)\b"),
    ("free_gift", r"\b(free gift|freebie|gift with|tote|sample)\b"),
    ("cash_saving", r"\b(cashback|discount|voucher|code|sale|% off|coupon|price match)\b|خصم|كوبون"),
]


def label_mock(texts: list[str], cb: dict) -> list[dict]:
    res = []
    for t in texts:
        low = t.lower()
        rt = next((lab for lab, pat in _RULES if re.search(pat, low)), "none")
        neg = re.search(r"(scam|con\b|waste|never win|rigged|pointless|fake)", low)
        pos = re.search(r"(love|great|brilliant|worth|recommend|saved|won\b)", low)
        stance = "negative" if neg else "positive" if pos else "neutral"
        mp = "yes" if re.search(r"(bills|cost of living|skint|afford|tight|cutting back|prices|salary|saving)", low) else "no"
        res.append({"reward_type": rt, "stance": stance, "money_pressure": mp, "evidence": "mock-rule"})
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=int, default=1)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="label only the first N posts (pilot)")
    args = ap.parse_args()

    cb = load_yaml("codebook.yaml")
    posts = pd.read_csv(DATA / "raw" / "posts.csv")
    if args.limit:
        posts = posts.head(args.limit)
    texts = posts["text"].astype(str).tolist()
    labels = label_mock(texts, cb) if args.mock else label_with_claude(texts, cb, args.model)
    out = pd.concat([posts[["id", "date", "country"]].reset_index(drop=True), pd.DataFrame(labels)], axis=1)
    out["labeller"] = "mock" if args.mock else args.model
    path = DATA / "labels" / f"claude_run{args.run}.csv"
    out.to_csv(path, index=False)
    print(f"saved {path} ({len(out)} posts)")


if __name__ == "__main__":
    main()
