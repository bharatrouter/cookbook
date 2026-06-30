#!/usr/bin/env python3
"""Merge ALL result shards and compute final cost+quality+latency tables with
Wilson 95% confidence intervals on the pass-rate (Wilson 1927 — the correct CI
for proportions near 1.0; see methodology-citations.md).

Cost uses the ACTUAL host each leg ran on, at dated/verified prices (prices.md). FX ₹96/$.
Run after the benchmark jobs finish:  python3 analyze.py
"""
import json, os, glob, math

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "results")
FX = 96

# ₹/Mtok (in, out) at the host actually used. Single open-model legs run on Baseten (fast host).
PRICE = {
    "opus":                    (480, 2400),  # $5/$25
    "gpt-5.5":                 (480, 2880),  # $5/$30
    "sonnet":                  (288, 1440),  # $3/$15
    "haiku":                   (96, 480),    # $1/$5
    "gpt-5.4-mini":            (72, 432),    # $0.75/$4.50
    "gpt-5.4-nano":            (19, 120),    # $0.20/$1.25
    "glm-5.2":                 (134, 422),   # Baseten zai-org/GLM-5.2 ($1.40/$4.40)
    "glm-4.7":                 (58, 211),    # Baseten zai-org/GLM-4.7 ($0.60/$2.20)
    "glm-4.5-air":             (12, 82),     # OpenRouter z-ai/glm-4.5-air
    "glm-4.7-flash":           (6, 38),      # OpenRouter z-ai/glm-4.7-flash
    "gpt-oss-120b":            (10, 48),     # Baseten openai/gpt-oss-120b ($0.10/$0.50)
    "nemotron-super":          (29, 72),     # Baseten nvidia/Nemotron-120B-A12B ($0.30/$0.75)
    # Consensus cost = SUM of all panel+verify+synth calls, priced at a BLENDED rate across the
    # Groq panel members (qwen3-32b/llama-3.3-70b/kimi-k2; glm-sangam anchors on GLM-4.7). Estimate.
    "bharatrouter/glm-sangam": (50, 180),    # GLM-4.7 anchor + Groq voices, blended
    "bharatrouter/open-sangam":(40, 130),    # Groq panel blend (llama-3.3-70b synth dominates)
    "bharatrouter/auto":       (6, 38),      # adaptive small open-weight; UPPER BOUND
}
LABEL = {
    "opus": "Claude Opus 4.8", "gpt-5.5": "GPT-5.5", "sonnet": "Claude Sonnet 4.6",
    "haiku": "Claude Haiku 4.5", "gpt-5.4-mini": "GPT-5.4-mini", "gpt-5.4-nano": "GPT-5.4-nano",
    "glm-5.2": "GLM-5.2 (Baseten)", "glm-4.7": "GLM-4.7 (Baseten)",
    "glm-4.5-air": "GLM-4.5-air", "glm-4.7-flash": "GLM-4.7-flash",
    "gpt-oss-120b": "gpt-oss-120B (Baseten)", "nemotron-super": "Nemotron-Super (Baseten)",
    "bharatrouter/glm-sangam": "GLM-Sangam", "bharatrouter/open-sangam": "Open-Sangam",
    "bharatrouter/auto": "Auto (adaptive)",
}
FRONTIER = ["opus", "gpt-5.5", "glm-5.2", "glm-4.7", "bharatrouter/glm-sangam"]
BUDGET = ["sonnet", "haiku", "gpt-5.4-mini", "gpt-5.4-nano", "glm-4.7-flash", "glm-4.5-air",
          "gpt-oss-120b", "nemotron-super", "bharatrouter/open-sangam"]
STD = {"is_prime","fib","reverse_words","is_anagram","binary_search","roman_to_int","lcp","valid_parentheses"}


def wilson(passes, n, z=1.96):
    """Wilson score 95% CI for a binomial proportion (handles p near 1.0)."""
    if n == 0:
        return (0.0, 0.0)
    p = passes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def load():
    merged = {}
    for p in sorted(glob.glob(os.path.join(R, "results-all-*.json"))):
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
    # Fair accuracy: a 429/timeout is infra, not a model mistake — exclude infra errors from
    # the denominator (uniform across legs; most have 0). Wilson CI on the effective N.
    errs = d.get("errors", 0)
    n_eff = max(1, d["tot_runs"] - errs)
    lo, hi = wilson(d["tot_pass"], n_eff)
    return {
        "leg": leg, "label": LABEL[leg],
        "acc": round(d["tot_pass"] / n_eff * 100, 1),
        "ci_lo": round(lo * 100, 1), "ci_hi": round(hi * 100, 1),
        "n": n_eff, "repeats": d.get("repeats"),
        "acc_std": round(sa * 100, 1), "acc_hard": round(ha * 100, 1),
        "lat": d["mean_lat_per_task"], "in": d["mean_in_per_task"], "out": d["mean_out_per_task"],
        "inr": round(cost, 3), "usd": round(cost / FX, 4), "errors": d.get("errors", 0),
    }


def show(title, legs, data):
    print(f"\n### {title}")
    print(f"{'System':24s} {'Acc%':>5s} {'95% CI':>13s} {'N':>5s} {'std/hard':>9s} {'lat':>7s} {'out':>6s} {'₹/task':>7s} {'$/task':>8s} {'errs':>5s}")
    rows = [row(l, data[l]) for l in legs if l in data]
    for r in rows:
        print(f"{r['label']:24s} {r['acc']:>5.1f} [{r['ci_lo']:>5.1f}-{r['ci_hi']:<5.1f}] {r['n']:>5d} "
              f"{r['acc_std']:>4.0f}/{r['acc_hard']:<4.0f} {r['lat']:>6.1f}s {r['out']:>6d} "
              f"{r['inr']:>7.3f} {r['usd']:>8.4f} {r['errors']:>5d}")
    missing = [l for l in legs if l not in data]
    if missing:
        print(f"  (pending: {missing})")
    return rows


def main():
    data = load()
    have = sorted(data.keys())
    print(f"systems present ({len(have)}): {have}")
    fr = show("Frontier tier", FRONTIER, data)
    bu = show("Budget tier", BUDGET, data)
    out = {"frontier": fr, "budget": bu, "fx": FX, "ci": "Wilson 95%"}
    json.dump(out, open(os.path.join(R, "final-tables.json"), "w"), indent=2)
    print("\nwrote results/final-tables.json")


if __name__ == "__main__":
    main()
