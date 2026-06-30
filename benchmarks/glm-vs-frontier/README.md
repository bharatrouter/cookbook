# GLM vs Frontier — a reproducible coding benchmark

This directory contains the **exact setup, scripts, prices and raw results** behind the
BharatRouter blog posts:

- [Can a GLM consensus replace a frontier model?](https://bharatrouter.com/blog/glm-vs-frontier)
- [The GLM host showdown — Baseten vs OpenRouter vs Zhipu](https://bharatrouter.com/blog/glm-host-showdown)
- [How we benchmark — and why you can trust the numbers](https://bharatrouter.com/blog/benchmark-methodology)

Everything here is runnable. Clone it, set your keys, and you should reproduce the same
tables (within run-to-run variance). Nothing is hand-tuned; the numbers in the blogs come
straight out of `results/`.

> **Why this exists:** benchmark claims are only as good as their reproducibility. The task
> set, the scoring (execution, not vibes), the prices (dated, sourced) and the raw outputs
> are all here so anyone can audit or re-run. **These are interim results on a 14-task set; a
> broader, contamination-controlled benchmark is coming.**

---

## What it measures

For each model/system, across **14 execution-checked coding tasks** (8 standard + 6 hard),
**100 repeats each — 1,400 results per system**:

- **Quality** — pass-rate (a task passes only if the generated code passes *all* its asserts),
  with a **Wilson 95% confidence interval**. Infrastructure errors (HTTP 429 / timeouts) are
  **excluded from the denominator** — a rate-limit is not a model mistake.
- **Latency** — mean wall-clock seconds per call
- **Tokens** — mean input/output tokens per task (drives cost)
- **Cost** — computed from the dated price sheet in [`prices.md`](./prices.md), from real tokens

Open models run on the host they're *meant* to run on — **GLM on Baseten**, the fast first-party
host. OpenAI and Anthropic legs hit their native APIs directly. One harness, one task set,
identical scoring for all.

## Replicate it

```bash
export BR_API_KEY=br-...              # https://bharatrouter.com  (GLM, open models, Sangam)
export OPENAI_API_KEY=sk-...          # only for the OpenAI legs
export ANTHROPIC_API_KEY=sk-ant-...   # only for the Anthropic legs

# frontier tier (GLM on Baseten):
TASKSET=all REPEATS=100 python3 benchmark.py opus gpt-5.5 glm-5.2 glm-4.7 bharatrouter/glm-sangam

# budget tier:
TASKSET=all REPEATS=100 python3 benchmark.py \
  sonnet haiku gpt-5.4-mini gpt-5.4-nano \
  gpt-oss-120b nemotron-super glm-4.5-air glm-4.7-flash bharatrouter/open-sangam

# then the tables (Wilson CIs, FX ₹96/$):
python3 analyze.py
```

`TASKSET` ∈ `standard` | `hard` | `all`. Keys are read from the environment only and never
written to disk. Provider rate limits are env-tunable: `WORKERS_BR`, `BACKOFF_START`,
`BACKOFF_CAP`, `MAX_ATTEMPTS`. **`APPEND=1`** accumulates a run onto the existing totals so you
can grow N over time (run N=50 today, `+50` next week → N=100; the CIs just tighten).

### Host benchmark (Blog 4)

`bench_hosts.py` runs the **same** GLM model across Baseten / Zhipu / OpenRouter and reports
TTFT, latency, throughput, cost and errors:

```bash
export BR_API_KEY=br-... OPENROUTER_KEY=sk-or-v1-...
REPEATS_HOST=20 python3 bench_hosts.py
```

## The tasks

Standard (8): `is_prime, fib, reverse_words, is_anagram, binary_search, roman_to_int, lcp, valid_parentheses`
Hard (6): `edit_distance, coin_change, trap (rain water), word_break, regex_match, min_window`

Each task ships with assert-based tests; a run "passes" only if the model's code block passes
every assert in a fresh subprocess (12s timeout). See `benchmark.py` for the exact prompts and tests.

## Consensus recipes (Sangam)

"Sangam" is BharatRouter's consensus mode: a **panel** answers, a **verifier** critiques, a
**synthesizer** reconciles one best answer. The open panels run on **Groq** (fast) with an
**OpenRouter failover**; `glm-sangam` anchors on GLM-4.7. The panel composition is published —
that's the reproducibility promise — and you can BYOK every member.

| Alias | Panel | Verifier | Synthesizer | Notes |
|---|---|---|---|---|
| `bharatrouter/glm-sangam` | GLM-4.7 (anchor) · Qwen3-32B · Llama-3.3-70B | Qwen3-32B | GLM-4.7 | Groq voices + Baseten anchor |
| `bharatrouter/open-sangam` | Qwen3-32B · Llama-3.3-70B · Kimi-K2 | Qwen3-32B | Llama-3.3-70B | Groq, + OpenRouter failover |

## Results

Conducted **2026-06-29 / 30**. Raw per-run JSON in [`results/`](./results/). Accuracy carries a
**Wilson 95% CI**; cost uses the host each leg actually ran on at the dated prices in
[`prices.md`](./prices.md), FX ₹96/$.

### Frontier tier

| System | Accuracy (95% CI) | std / hard | Latency | ₹ / task |
|---|---|---|---|---|
| Claude Opus 4.8 | 100% [99.7–100] | 100 / 100 | 2.9s | ₹0.395 |
| GPT-5.5 | 100% [99.7–100] | 100 / 100 | 2.5s | ₹0.440 |
| **GLM-4.7** (Baseten) | **99.9% [99.5–100]** | 98 / 98 | **1.5s** | **₹0.033** |
| **GLM-5.2** (Baseten) | **99.4% [98.9–99.7]** | 100 / 99 | **1.4s** | ₹0.055 |
| GLM-Sangam (consensus, N=140) | 97.1% [92.9–98.9] | 98 / 97 | 6.2s | ₹0.143 |

Quality at parity — and on **Baseten, GLM is *faster*** than the frontier (1.4–1.5s vs 2.5–2.9s)
at ~a tenth the cost. The "GLM is slow" reputation is a *host* artifact (a generic endpoint at
~20s), not the model.

### Budget tier

| System | Accuracy (95% CI) | std / hard | Latency | ₹ / task |
|---|---|---|---|---|
| **gpt-oss-120B** (Baseten) | **99.6% [99.1–99.8]** | 98 / 99 | 5.7s | **₹0.014** |
| GPT-5.4-nano | 99.8% [99.4–99.9] | 100 / 100 | 2.0s | ₹0.018 |
| GPT-5.4-mini | 100% [99.7–100] | 100 / 100 | 1.6s | ₹0.052 |
| GLM-4.7-flash (open, N=140) | 99.3% [96.1–99.9] | 100 / 98 | 17.8s | ₹0.049 |
| GLM-4.5-air (open, N=137) | 98.5% [94.8–99.6] | 100 / 92 | 16.7s | ₹0.095 |
| Open-Sangam (consensus, N=700) | 99.3% [98.3–99.7] | 100 / 98 | 11.0s | ₹0.918 |
| Claude Sonnet 4.6 | 100% [99.7–100] | 100 / 100 | 3.9s | ₹0.318 |
| Claude Haiku 4.5 | 83.4% [81.4–85.3] | 98 / 64 | 3.6s | ₹0.224 |
| Nemotron-Super (Baseten) | 75.8% [73.5–78.0] | 73 / 79 | 1.8s | ₹0.023 |

**The cheapest thing here is open**: gpt-oss-120B at ₹0.014/task and 99.6%. Consensus buys
*reliability*, not cheapness (Open-Sangam ₹0.918 — a verified panel spends more tokens).

### Host showdown (same model, three hosts — Blog 4)

| Host — GLM-5.2 | Latency | Eff. tok/s | ₹ / task | Errors |
|---|---|---|---|---|
| Baseten (first-party) | ~1.4s* | — | ₹0.055 | 0 |
| OpenRouter | 4.1s | 173 | ₹0.30 | 0 |
| Zhipu (the source) | 13.5s | 52 | ₹0.30 | 0 |

\* Baseten figure from the 1,400-run coding benchmark (shorter outputs); its long-output streaming
cell is interim (the account hit a billing pause mid-run — any single host can blip, which is the
argument for routing). OpenRouter/Zhipu are 20 streaming runs each on identical GLM-5.2.

### Field notes (reproducibility includes the hiccups)

- At concurrency, the GLM-on-Zhipu legs hit Zhipu's rate limit (`HTTP 429`, code 1302); GLM-4.5-air's
  full N=1400 run was throttle-degraded (29s latency) and **quarantined** in favour of a clean N=137.
- Baseten returned `HTTP 402` mid-study (account billing) — measured Baseten numbers are from before
  that, and the host cell is marked interim.
- These are exactly why you'd run BharatRouter's **failover + circuit breaker** in production rather
  than pin one host. The harness measures hosts in isolation *on purpose*.

Methodology (scoring, CIs, citations): [the methodology post](https://bharatrouter.com/blog/benchmark-methodology).

---

*Part of the [BharatRouter cookbook](https://github.com/bharatrouter/cookbook). Go live in one
command: [BharatRouter Code](https://bharatrouter.com/blog/bharatrouter-code).*
