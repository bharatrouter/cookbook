# Price sheet

All cost figures in the benchmark are computed from this table — **official list prices,
fetched 2026-06-30**. INR conversions use **FX ₹96 / $1** (stated, not hidden). Re-verify the
sources before quoting; prices move. Cost in the blogs is computed from the **real measured
tokens** (recorded in `results/`), never list-price guesses.

## Frontier & budget closed (OpenAI / Anthropic — native APIs)

| Model | Model id | $/Mtok in | $/Mtok out | ₹/Mtok in | ₹/Mtok out | Source |
|---|---|---|---|---|---|---|
| Claude Opus 4.8 | `claude-opus-4-8` | 5.00 | 25.00 | 480 | 2400 | [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | 3.00 | 15.00 | 288 | 1440 | [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| Claude Haiku 4.5 | `claude-haiku-4-5` | 1.00 | 5.00 | 96 | 480 | [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| GPT-5.5 | `gpt-5.5` | 5.00 | 30.00 | 480 | 2880 | [OpenAI pricing](https://developers.openai.com/api/docs/pricing) |
| GPT-5.4-mini | `gpt-5.4-mini` | 0.75 | 4.50 | 72 | 432 | [OpenAI pricing](https://developers.openai.com/api/docs/pricing) |
| GPT-5.4-nano | `gpt-5.4-nano` | 0.20 | 1.25 | 19 | 120 | [OpenAI pricing](https://developers.openai.com/api/docs/pricing) |

## Open models (via BharatRouter — INR-native catalog)

Each open model runs on the host it's *meant* to run on. GLM's fast first-party host is
**Baseten**; the same model id can also route to Zhipu (the source) or OpenRouter (BYOK).

| Model | Model id | Host | ₹/Mtok in | ₹/Mtok out | $/Mtok in | $/Mtok out |
|---|---|---|---|---|---|---|
| **GLM-4.7** | `glm-4.7` | **Baseten** | 58 | 211 | 0.60 | 2.20 |
| GLM-4.7 | `glm-4.7` | Zhipu | 58 | 211 | 0.60 | 2.20 |
| GLM-4.7 | `glm-4.7` | OpenRouter (BYOK) | 38 | 168 | 0.40 | 1.75 |
| **GLM-5.2** | `glm-5.2` | **Baseten** | 134 | 422 | 1.40 | 4.40 |
| GLM-5.2 | `glm-5.2` | Zhipu / OpenRouter | 134 | 422 | 1.40 | 4.40 |
| **gpt-oss-120B** | `gpt-oss-120b` | **Baseten** | 10 | 48 | 0.10 | 0.50 |
| Nemotron-Super | `nemotron-super` | Baseten | 29 | 72 | 0.30 | 0.75 |
| GLM-4.5-air | `glm-4.5-air` | OpenRouter | 12 | 82 | 0.12 | 0.85 |
| GLM-4.7-flash | `glm-4.7-flash` | Zhipu / OpenRouter | 6 | 38 | 0.06 | 0.40 |

Source: BharatRouter model catalog (`src/catalog.ts`), $ at FX ₹96/$.

## Sangam (consensus) cost basis

Sangam runs multiple models per request, so its cost is the **sum of all member calls**
(panel + verifier + synthesizer). The harness records the *total* tokens BharatRouter reports
for the consensus call; cost is those real total tokens priced at a **blended rate across the
Groq panel members** (qwen3-32b / llama-3.3-70b / kimi-k2; `glm-sangam` anchors on GLM-4.7).
This is an **estimate**, labelled wherever a Sangam cost appears.

| Consensus | Panel (Groq) | Blended ₹/Mtok in | Blended ₹/Mtok out |
|---|---|---|---|
| `open-sangam` | qwen3-32b · llama-3.3-70b · kimi-k2 | 40 | 130 |
| `glm-sangam` | glm-4.7 (anchor) · qwen3-32b · llama-3.3-70b | 50 | 180 |

> A verified panel spends far more tokens than a single model, so Sangam is a **reliability**
> play, not a cheap one — the cost reflects that honestly.
