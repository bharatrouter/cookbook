# GLM vs Frontier — a reproducible coding benchmark

This directory contains the **exact setup, scripts, prices and raw results** behind the
BharatRouter blog posts:

- [The GLM host showdown — Baseten vs OpenRouter vs Zhipu](https://bharatrouter.com/blog/glm-host-showdown)
- [Can a GLM consensus replace a frontier model?](https://bharatrouter.com/blog/glm-vs-frontier) *(Blog 3)*

Everything here is runnable. Clone it, set your keys, and you should reproduce the same
tables (within run-to-run variance). Nothing is hand-tuned; the numbers in the blogs come
straight out of `results/`.

> **Why this exists:** benchmark claims are only as good as their reproducibility. The task
> set, the scoring (execution, not vibes), the prices (dated, sourced) and the raw outputs
> are all here so anyone can audit or re-run.

---

## What it measures

For each model/system, across **14 execution-checked coding tasks** (8 standard + 6 hard),
**10 repeats each**:

- **Quality** — pass-rate (a task passes only if the generated code passes *all* its asserts)
- **Latency** — mean wall-clock seconds per call
- **Tokens** — mean input/output tokens per task (drives cost)
- **Cost** — computed from the dated price sheet in [`prices.md`](./prices.md), not assumed

Two tiers:

| Tier | Systems |
|---|---|
| **Frontier** | GLM-4.6 · GLM-Sangam · GPT-5.5 · Claude Opus 4.8 |
| **Budget** | GLM-4.5-air · GLM-4.7-flash · Open-Sangam · Auto · Haiku 4.5 · Sonnet 4.6 · GPT-5.4-mini · GPT-5.4-nano |

The GLM single + Sangam legs route through **BharatRouter**; OpenAI and Anthropic legs hit
their native APIs directly (Opus/GPT aren't in BharatRouter's catalog). One harness, one
task set, identical scoring for all.

## Replicate it

```bash
export BR_API_KEY=br-...              # https://bharatrouter.com  (GLM + Sangam legs)
export OPENAI_API_KEY=sk-...          # only for the OpenAI legs
export ANTHROPIC_API_KEY=sk-ant-...   # only for the Anthropic legs

# one tier:
TASKSET=all REPEATS=10 python3 benchmark.py opus gpt-5.5 glm-4.6 bharatrouter/glm-sangam

# everything:
TASKSET=all REPEATS=10 python3 benchmark.py \
  opus gpt-5.5 glm-4.6 bharatrouter/glm-sangam \
  sonnet haiku gpt-5.4-mini gpt-5.4-nano \
  glm-4.5-air glm-4.7-flash bharatrouter/open-sangam bharatrouter/auto
```

`TASKSET` ∈ `standard` | `hard` | `all`. Keys are read from the environment only and never
written to disk; results land in `results/results-<taskset>-r<N>.json`.

## The tasks

Standard (8): `is_prime, fib, reverse_words, is_anagram, binary_search, roman_to_int, lcp, valid_parentheses`
Hard (6): `edit_distance, coin_change, trap (rain water), word_break, regex_match, min_window`

Each task ships with assert-based tests; a run "passes" only if the model's code block passes
every assert in a fresh subprocess (12s timeout). See `benchmark.py` for the exact prompts and tests.

## Consensus recipes (Sangam)

"Sangam" is BharatRouter's consensus mode: a **panel** answers, a **verifier** critiques, a
**synthesizer** reconciles one best answer. Call it like any model id. The panel composition is
published (that's the reproducibility promise) and you can BYOK every member.

```bash
# GLM-anchored consensus (frontier tier)
curl https://api.bharatrouter.com/v1/chat/completions \
  -H "Authorization: Bearer $BR_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"bharatrouter/glm-sangam","messages":[{"role":"user","content":"..."}]}'
```

| Alias | Panel | Verifier | Synthesizer | Residency |
|---|---|---|---|---|
| `bharatrouter/glm-sangam` | GLM-4.7 · Qwen2.5-7B · Llama-3.1-8B | Qwen2.5-7B | GLM-4.7 | global, open-weight |
| `bharatrouter/open-sangam` | Qwen2.5-7B · Llama-3.1-8B · Qwen2.5-VL-7B | Qwen2.5-7B | Llama-3.1-8B | India, open-weight |
| `bharatrouter/auto` | adaptive — one fast model on easy asks, escalates to the open panel on hard ones | Qwen2.5-7B | Llama-3.1-8B | India, open-weight |
| `bharatrouter/sangam` | GPT-5 · Gemini-2.5-Flash · Claude-Haiku-4.5 | Claude-Haiku-4.5 | GPT-5-mini | global, mixed |

## Prices

All cost numbers come from [`prices.md`](./prices.md) — official, dated, sourced. We do **not**
bake prices into the harness, so the price sheet can be re-verified independently.

## Results

Conducted **2026-06-29 / 30**. Raw per-run JSON in [`results/`](./results/). Cost uses the host
each leg actually ran on (GLM single legs via OpenRouter), at the dated prices in `prices.md`,
FX ₹96/$.

### Frontier tier

| System | Accuracy | std / hard | Latency | ₹ / task | $ / task |
|---|---|---|---|---|---|
| Claude Opus 4.8 | 100% | 100 / 100 | 2.8s | ₹0.39 | $0.0041 |
| GPT-5.5 | 100% | 100 / 100 | 3.3s | ₹0.43 | $0.0045 |
| **GLM-4.6** (open) | **99.3%** | 99 / 100 | 19.9s | **₹0.14** | $0.0014 |
| **GLM-Sangam** (consensus) | 97.1% | 98 / 97 | 6.2s | ₹0.17 | $0.0017 |

Quality at parity; GLM ~⅓ the cost; frontier wins on latency. Sangam ≈ Opus quality, cheaper,
and 3× faster than single GLM.

### Budget tier

| System | Accuracy | std / hard | Latency | ₹ / task |
|---|---|---|---|---|
| GPT-5.4-nano | 100% | 100 / 100 | 2.1s | ₹0.018 |
| GPT-5.4-mini | 100% | 100 / 100 | 1.4s | ₹0.053 |
| Claude Sonnet 4.6 | 100% | 100 / 100 | 4.0s | ₹0.314 |
| GLM-4.7-flash (open) | 99.3% | 100 / 98 | 17.8s | ₹0.049 |
| GLM-4.5-air (open) | 96.4% | 100 / 92 | 16.7s | ₹0.095 |
| Open-Sangam (consensus) | 93.6% | 99 / 87 | 8.3s | ₹0.032 |
| Auto (adaptive) | 92.1% | 99 / 83 | 12.0s | ₹0.056 |
| Claude Haiku 4.5 | 79.3% | 98 / 55 | 3.5s | ₹0.227 |

GPT-5.4-nano: cheapest *and* perfect. Open GLM stays competitive (latency aside). Haiku 4.5
collapses on the hard tier (55%).

### A field note (reproducibility includes the hiccups)

At concurrency, the GLM legs hit Zhipu's free-tier rate limit (`HTTP 429`, code 1302). We
routed the single-GLM legs via OpenRouter BYOK + added backoff for clean per-host numbers. In
production the answer is BharatRouter's failover + circuit breaker — a rate-limited host rolls
to the next transparently. The harness here measures hosts in isolation *on purpose*; the
router is what you'd actually run. (See `WORKERS_BR` and the 429 backoff in `benchmark.py`.)

Full writeup: [the blog post](https://bharatrouter.com/blog/glm-vs-frontier).

---

*Part of the [BharatRouter cookbook](https://github.com/bharatrouter/cookbook).*
