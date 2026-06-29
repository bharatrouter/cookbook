#!/usr/bin/env python3
"""Merge the two result files and compute the final cost+quality+latency tables.
Cost uses the ACTUAL host each leg ran on, at verified prices (see prices.md). FX ₹96/$.
Run after both benchmark runs finish:  python3 analyze.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "results")
FX = 96

# ₹/Mtok (in, out) at the host actually used. GLM single legs ran via OpenRouter (BYOK).
PRICE = {
    "opus":                    (480, 2400),  # $5/$25
    "gpt-5.5":                 (480, 2880),  # $5/$30
    "sonnet":                  (288, 1440),  # $3/$15
    "haiku":                   (96, 480),    # $1/$5
    "gpt-5.4-mini":            (72, 432),    # $0.75/$4.50
    "gpt-5.4-nano":            (19, 120),    # $0.20/$1.25
    "glm-4.6":                 (41, 167),    # OpenRouter z-ai/glm-4.6
    "glm-4.5-air":             (12, 82),     # OpenRouter z-ai/glm-4.5-air
    "glm-4.7-flash":           (6, 38),      # OpenRouter z-ai/glm-4.7-flash
    "bharatrouter/glm-sangam": (58, 211),    # priced at GLM-4.7 anchor (UPPER BOUND; Qwen/Llama cheaper)
    "bharatrouter/open-sangam":(6, 38),      # small open-weight panel; flash-equiv UPPER BOUND
    "bharatrouter/auto":       (6, 38),      # adaptive small open-weight; UPPER BOUND
}
LABEL = {
    "opus": "Claude Opus 4.8", "gpt-5.5": "GPT-5.5", "sonnet": "Claude Sonnet 4.6",
    "haiku": "Claude Haiku 4.5", "gpt-5.4-mini": "GPT-5.4-mini", "gpt-5.4-nano": "GPT-5.4-nano",
    "glm-4.6": "GLM-4.6 (single)", "glm-4.5-air": "GLM-4.5-air", "glm-4.7-flash": "GLM-4.7-flash",
    "bharatrouter/glm-sangam": "GLM-Sangam", "bharatrouter/open-sangam": "Open-Sangam",
    "bharatrouter/auto": "Auto (adaptive)",
}
FRONTIER = ["opus", "gpt-5.5", "glm-4.6", "bharatrouter/glm-sangam"]
BUDGET = ["sonnet", "haiku", "gpt-5.4-mini", "gpt-5.4-nano", "glm-4.5-air", "glm-4.7-flash",
          "bharatrouter/open-sangam", "bharatrouter/auto"]
STD = {"is_prime","fib","reverse_words","is_anagram","binary_search","roman_to_int","lcp","valid_parentheses"}

def load():
    merged = {}
    for fn in ("results-all-r10.json", "results-all-r10-api.json"):
        p = os.path.join(R, fn)
        if os.path.exists(p):
            merged.update(json.load(open(p)))
    return merged

def tier_split_acc(d):
    std = [t for n, t in d["tasks"].items() if n in STD]
    hard = [t for n, t in d["tasks"].items() if n not in STD]
    sa = sum(t["passes"] for t in std) / max(1, sum(t["runs"] for t in std))
    ha = sum(t["passes"] for t in hard) / max(1, sum(t["runs"] for t in hard))
    return sa, ha

def row(leg, d):
    pin, pout = PRICE[leg]
    cost = d["mean_in_per_task"] * pin / 1e6 + d["mean_out_per_task"] * pout / 1e6
    sa, ha = tier_split_acc(d)
    return {
        "leg": leg, "label": LABEL[leg],
        "acc": round(d["overall_pass_rate"] * 100, 1),
        "acc_std": round(sa * 100, 1), "acc_hard": round(ha * 100, 1),
        "lat": d["mean_lat_per_task"], "in": d["mean_in_per_task"], "out": d["mean_out_per_task"],
        "inr": round(cost, 3), "usd": round(cost / FX, 4), "errors": d.get("errors", 0),
    }

def show(title, legs, data):
    print(f"\n### {title}")
    print(f"{'System':24s} {'Acc%':>5s} {'std/hard':>9s} {'lat/task':>9s} {'out tok':>8s} {'₹/task':>7s} {'$/task':>8s} {'errs':>5s}")
    rows = [row(l, data[l]) for l in legs if l in data]
    for r in rows:
        print(f"{r['label']:24s} {r['acc']:>5.1f} {r['acc_std']:>4.0f}/{r['acc_hard']:<4.0f} "
              f"{r['lat']:>8.1f}s {r['out']:>8d} {r['inr']:>7.3f} {r['usd']:>8.4f} {r['errors']:>5d}")
    return rows

def main():
    data = load()
    have = sorted(data.keys())
    print(f"systems present ({len(have)}): {have}")
    missing = [l for l in FRONTIER + BUDGET if l not in data]
    if missing:
        print(f"!! MISSING (run not finished?): {missing}")
    fr = show("Frontier tier", FRONTIER, data)
    bu = show("Budget tier", BUDGET, data)
    json.dump({"frontier": fr, "budget": bu}, open(os.path.join(R, "final-tables.json"), "w"), indent=2)
    print("\nwrote results/final-tables.json")

if __name__ == "__main__":
    main()
